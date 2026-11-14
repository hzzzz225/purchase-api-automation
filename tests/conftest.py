import pytest
import requests
from config.settings import BASE_URL,USERNAME,PASSWORD,REQUEST_TIMEOUT
from api.client import ApiClient
from api.purchase_order_api import PurchaseOrderApi
from utils.database import Database


@pytest.fixture
def token():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": USERNAME,
            "password": PASSWORD
        },
        timeout=REQUEST_TIMEOUT
    )

    assert response.status_code == 200

    return response.json()["access_token"]

@pytest.fixture
def api_client(token):
    client = ApiClient(token=token)

    yield client

    client.close()

@pytest.fixture
def purchase_api(api_client):
    return PurchaseOrderApi(api_client)

@pytest.fixture
def db():
    database = Database()
    yield database
    database.close()