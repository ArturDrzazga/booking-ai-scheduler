import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.service import Service
from app.models.settings import Settings
from app.models.staff import Staff
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Creates an in-memory SQLite database engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Provides a database session for tests."""
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """Provides an HTTP client connected to the test application."""
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_settings(db_session):
    """Creates default system settings."""
    settings = Settings(id=1, salon_name="Test Salon", email_notifications=True)
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(settings)
    return settings


@pytest_asyncio.fixture
async def test_service(db_session):
    """Creates a test service."""
    service = Service(name="Strzyżenie", price=100.0, duration_time=60)
    db_session.add(service)
    await db_session.commit()
    await db_session.refresh(service)
    return service


@pytest_asyncio.fixture
async def test_staff(db_session):
    """Creates a test staff member."""
    staff = Staff(name="Anna Kowalska", bio="Fryzjerka")
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)
    return staff


@pytest_asyncio.fixture
async def normal_user(db_session):
    """Creates a verified regular user."""
    user = User(
        email="klient@test.pl",
        hashed_password=get_password_hash("haslo123"),
        phone_number="111222333",
        is_verified=True,
        is_guest=False,
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session):
    """Creates an admin user."""
    admin = User(
        email="admin@test.pl",
        hashed_password=get_password_hash("admin123"),
        phone_number="999888777",
        is_verified=True,
        is_guest=False,
        is_admin=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
def user_token(normal_user):
    """Returns a JWT token for a regular user."""
    return create_access_token({"sub": normal_user.email})


@pytest_asyncio.fixture
def admin_token(admin_user):
    """Returns a JWT token for an admin user."""
    return create_access_token({"sub": admin_user.email})