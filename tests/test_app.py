import pytest
from app import app
from models import db, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/test_db'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_home_page(client):
    """Test that home page loads correctly"""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Login' in rv.data

def test_login_page(client):
    """Test login page access"""
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'Username' in rv.data
    assert b'Password' in rv.data

def test_register_user(client):
    """Test user registration"""
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }
    rv = client.post('/register', data=data, follow_redirects=True)
    assert rv.status_code == 200
    assert User.query.filter_by(username='testuser').first() is not None
