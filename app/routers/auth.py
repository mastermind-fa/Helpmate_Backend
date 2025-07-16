from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token
from app.models.user import User, PasswordReset, EmailVerificationToken
from app.models.worker import Worker
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate, ChangePasswordRequest as UserChangePasswordRequest, ForgotPasswordRequest as UserForgotPasswordRequest, ResetPasswordRequest as UserResetPasswordRequest
from app.schemas.worker import WorkerCreate, WorkerLogin, WorkerResponse, WorkerUpdate, ChangePasswordRequest as WorkerChangePasswordRequest, ForgotPasswordRequest as WorkerForgotPasswordRequest, ResetPasswordRequest as WorkerResetPasswordRequest
from app.services.worker_service import WorkerService
from app.services.email_service import email_service
import os
import asyncio

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_public_image_url(image_path: str, request: Request) -> str:
    if not image_path:
        return None
    # If already a URL, return as is
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path
    # If already a /static/ path, return full URL
    if image_path.startswith("/static/"):
        return f"{request.url.scheme}://{request.url.netloc}{image_path}"
    # Otherwise, treat as filename in static
    filename = os.path.basename(image_path)
    return f"{request.url.scheme}://{request.url.netloc}/static/{filename}"


@router.post("/register/user", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Register a new user"""
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        phone_number=user.phone_number,
        address=user.address,
        is_verified=False,
        is_active=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Create verification token and send email
    token_record = email_service.create_verification_token(db, db_user.id, "user")
    if background_tasks is not None:
        background_tasks.add_task(
            lambda: asyncio.run(email_service.send_verification_email(db_user.email, token_record.token, "user"))
        )
    return db_user


@router.post("/register/worker", response_model=WorkerResponse)
def register_worker(worker: WorkerCreate, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Register a new worker with automatic service creation. Now supports category_id for direct category selection."""
    # Check if email already exists
    db_worker = db.query(Worker).filter(Worker.email == worker.email).first()
    if db_worker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create worker with services using the service
    worker_data = worker.dict()
    worker_data['hashed_password'] = get_password_hash(worker.password)
    worker_data['is_verified'] = False
    worker_data['is_active'] = False
    
    try:
        db_worker = WorkerService.create_worker_with_services(db, worker_data)
        # Create verification token and send email
        token_record = email_service.create_verification_token(db, db_worker.id, "worker")
        if background_tasks is not None:
            background_tasks.add_task(
                lambda: asyncio.run(email_service.send_verification_email(db_worker.email, token_record.token, "worker"))
            )
        return db_worker
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating worker: {str(e)}"
        )


@router.post("/login/user", response_model=Token)
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login for users"""
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Only allow login if is_active is True and (is_verified is True or is_active is True)
    if not user.is_active and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not activated or email not verified."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    if not user.is_verified and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email or wait for admin activation."
        )
    access_token = create_access_token(
        data={"sub": user.email, "user_type": "user", "user_id": user.id}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "user",
        "user_id": user.id
    }


@router.post("/login/worker", response_model=Token)
def login_worker(worker_credentials: WorkerLogin, db: Session = Depends(get_db)):
    """Login for workers"""
    worker = db.query(Worker).filter(Worker.email == worker_credentials.email).first()
    if not worker or not verify_password(worker_credentials.password, worker.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Only allow login if is_active is True and (is_verified is True or is_active is True)
    if not worker.is_active and not worker.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not activated or email not verified."
        )
    if not worker.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive worker"
        )
    if not worker.is_verified and not worker.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email or wait for admin activation."
        )
    access_token = create_access_token(
        data={"sub": worker.email, "user_type": "worker", "user_id": worker.id}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "worker",
        "user_id": worker.id
    }


@router.post("/forgot-password/user")
async def forgot_password_user(request: UserForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email for user"""
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a reset code has been sent."}
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive"
        )
    
    try:
        # Create reset record
        reset_record = email_service.create_reset_record(db, request.email, "user")
        
        # Send email
        email_sent = await email_service.send_reset_email(
            request.email, 
            reset_record.reset_code, 
            "user"
        )
        
        if email_sent:
            return {"message": "Password reset code sent to your email."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/forgot-password/worker")
async def forgot_password_worker(request: WorkerForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email for worker"""
    # Check if worker exists
    worker = db.query(Worker).filter(Worker.email == request.email).first()
    if not worker:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a reset code has been sent."}
    
    if not worker.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive"
        )
    
    try:
        # Create reset record
        reset_record = email_service.create_reset_record(db, request.email, "worker")
        
        # Send email
        email_sent = await email_service.send_reset_email(
            request.email, 
            reset_record.reset_code, 
            "worker"
        )
        
        if email_sent:
            return {"message": "Password reset code sent to your email."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/reset-password/user")
async def reset_password_user(request: UserResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset user password using reset code"""
    # Verify reset code
    reset_record = email_service.verify_reset_code(
        db, request.email, request.reset_code, "user"
    )
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )
    
    # Get user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Update password
        user.hashed_password = get_password_hash(request.new_password)
        
        # Mark reset code as used
        email_service.mark_reset_code_used(db, reset_record)
        
        db.commit()
        
        return {"message": "Password reset successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting password: {str(e)}"
        )


@router.post("/reset-password/worker")
async def reset_password_worker(request: WorkerResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset worker password using reset code"""
    # Verify reset code
    reset_record = email_service.verify_reset_code(
        db, request.email, request.reset_code, "worker"
    )
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )
    
    # Get worker
    worker = db.query(Worker).filter(Worker.email == request.email).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    try:
        # Update password
        worker.hashed_password = get_password_hash(request.new_password)
        
        # Mark reset code as used
        email_service.mark_reset_code_used(db, reset_record)
        
        db.commit()
        
        return {"message": "Password reset successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting password: {str(e)}"
        )


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    user_type: str = payload.get("user_type")
    
    if email is None or user_type is None:
        raise credentials_exception
    
    if user_type == "user":
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        return user
    elif user_type == "worker":
        worker = db.query(Worker).filter(Worker.email == email).first()
        if worker is None:
            raise credentials_exception
        return worker
    else:
        raise credentials_exception


@router.get("/user/profile", response_model=UserResponse)
async def get_user_profile(request: Request, current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access this endpoint"
        )
    # Patch image field to public URL
    user_dict = current_user.__dict__.copy()
    user_dict["image"] = get_public_image_url(current_user.image, request) if current_user.image else None
    return user_dict


@router.put("/user/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's profile"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access this endpoint"
        )
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    # Patch image field to public URL
    user_dict = current_user.__dict__.copy()
    user_dict["image"] = get_public_image_url(current_user.image, request) if current_user.image else None
    return user_dict 


@router.post("/user/upload-profile-image")
async def upload_profile_image(request: Request, file: UploadFile = File(...)):
    """Upload a profile image for the user. Returns the public URL."""
    # Save file to static directory
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'static')
    os.makedirs(static_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"user_{os.urandom(8).hex()}{file_ext}"
    file_path = os.path.join(static_dir, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    public_url = f"{request.url.scheme}://{request.url.netloc}/static/{filename}"
    return {"url": public_url} 


@router.get("/worker/profile", response_model=WorkerResponse)
async def get_worker_profile(request: Request, current_user: Worker = Depends(get_current_user)):
    """Get current worker's profile"""
    if not isinstance(current_user, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access this endpoint"
        )
    worker_dict = current_user.__dict__.copy()
    worker_dict["image"] = get_public_image_url(current_user.image, request) if current_user.image else None
    return worker_dict

@router.put("/worker/profile", response_model=WorkerResponse)
async def update_worker_profile(
    worker_update: WorkerUpdate,
    request: Request,
    current_user: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update worker's profile"""
    if not isinstance(current_user, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access this endpoint"
        )
    for field, value in worker_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    worker_dict = current_user.__dict__.copy()
    worker_dict["image"] = get_public_image_url(current_user.image, request) if current_user.image else None
    return worker_dict


@router.post("/worker/upload-profile-image")
async def upload_worker_profile_image(request: Request, file: UploadFile = File(...)):
    """Upload a profile image for the worker. Returns the public URL."""
    # Save file to static directory
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'static')
    os.makedirs(static_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"worker_{os.urandom(8).hex()}{file_ext}"
    file_path = os.path.join(static_dir, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    public_url = f"{request.url.scheme}://{request.url.netloc}/static/{filename}"
    return {"url": public_url}


@router.post("/user/change-password")
async def change_user_password(
    data: UserChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    if not isinstance(current_user, User):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can access this endpoint"
        )
    
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/worker/change-password")
async def change_worker_password(
    data: WorkerChangePasswordRequest,
    current_user: Worker = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change worker password"""
    if not isinstance(current_user, Worker):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access this endpoint"
        )
    
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"} 


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    # Try user first
    record = email_service.verify_email_token(db, token, "user")
    if record:
        user = db.query(User).filter(User.id == record.user_id).first()
        if user:
            user.is_verified = True
            user.is_active = True
            email_service.mark_verification_token_used(db, record)
            db.commit()
            return {"message": "Email verified successfully. You can now log in."}
    # Try worker
    record = email_service.verify_email_token(db, token, "worker")
    if record:
        from app.models.worker import Worker
        worker = db.query(Worker).filter(Worker.id == record.user_id).first()
        if worker:
            worker.is_verified = True
            worker.is_active = True
            email_service.mark_verification_token_used(db, record)
            db.commit()
            return {"message": "Email verified successfully. You can now log in."}
    raise HTTPException(status_code=400, detail="Invalid or expired verification token.") 


@router.post("/logout")
def logout():
    """Logout endpoint for frontend to call. JWT tokens are stateless, so logout is handled client-side by deleting the token."""
    return {"message": "Logged out successfully."} 