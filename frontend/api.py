
import os
import requests
import streamlit as st


class APIError(Exception):
    pass


def get_api_base_url():
    """Get FastAPI URL from Streamlit Secrets or environment."""

    try:
        url = st.secrets.get("API_BASE_URL", "")
    except Exception:
        url = ""

    if not url:
        url = os.getenv("API_BASE_URL", "")

    if not url:
        raise APIError(
            "Backend URL is not configured. "
            "Please add API_BASE_URL in Streamlit Secrets."
        )

    return url.rstrip("/")


def api_request(method, endpoint, token=None, data=None, params=None):

    base_url = get_api_base_url()
    url = f"{base_url}{endpoint}"

    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=20
        )

        if response.status_code >= 400:
            try:
                error = response.json()
                message = error.get(
                    "detail", "API request failed"
                )
            except ValueError:
                message = response.text or "API request failed"

            raise APIError(
                f"Error {response.status_code}: {message}"
            )

        if response.content:
            try:
                return response.json()
            except ValueError:
                raise APIError("Invalid response received from backend.")

        return {}

    except requests.exceptions.ConnectionError:
        raise APIError(
            "Cannot connect to FastAPI backend. "
            "Check whether your backend is deployed and running."
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
