
import requests

API_BASE_URL = "http://127.0.0.1:8000"


class APIError(Exception):
    pass


def api_request(method, endpoint, token=None, data=None, params=None):

    url = f"{API_BASE_URL}{endpoint}"

    headers = {}

    # Attach JWT token when user is logged in
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=15
        )

        if response.status_code >= 400:
            try:
                error = response.json()
                message = error.get("detail", "API request failed")
            except ValueError:
                message = response.text or "API request failed"

            raise APIError(
                f"Error {response.status_code}: {message}"
            )

        if response.content:
            return response.json()

        return {}

    except requests.exceptions.ConnectionError:
        raise APIError(
            "Cannot connect to FastAPI. Start your backend first."
        )

    except requests.exceptions.Timeout:
        raise APIError(
            "The API request timed out. Please try again."
        )

    except requests.exceptions.RequestException as error:
        raise APIError(str(error))


def login_user(email, password):

    return api_request(
        "POST",
        "/auth/login",
        data={
            "email": email,
            "password": password
        }
    )


def register_student(email, password, member_id):

    return api_request(
        "POST",
        "/auth/register",
        data={
            "email": email,
            "password": password,
            "role": "student",
            "member_id": member_id
        }
    )
