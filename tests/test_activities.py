from fastapi.testclient import TestClient
from src import app as app_module
from src.app import app, activities

client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # Expect at least some known activities present
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"].get("participants"), list)


def test_signup_and_duplicate():
    activity_name = "Chess Club"
    test_email = "test_add@example.com"

    # Ensure not already present
    if test_email in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].remove(test_email)

    # Signup should succeed
    resp = client.post(f"/activities/{activity_name}/signup?email={test_email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")
    assert test_email in activities[activity_name]["participants"]

    # Duplicate signup should be rejected
    resp2 = client.post(f"/activities/{activity_name}/signup?email={test_email}")
    assert resp2.status_code == 400
    assert resp2.json().get("detail") == "Student is already signed up"

    # Cleanup
    activities[activity_name]["participants"].remove(test_email)


def test_capacity_limit():
    # Create a temporary activity with max 1 participant
    tmp_name = "Test Capacity"
    activities[tmp_name] = {
        "description": "Temporary",
        "schedule": "Now",
        "max_participants": 1,
        "participants": []
    }

    email1 = "a@example.com"
    email2 = "b@example.com"

    r1 = client.post(f"/activities/{tmp_name}/signup?email={email1}")
    assert r1.status_code == 200

    r2 = client.post(f"/activities/{tmp_name}/signup?email={email2}")
    assert r2.status_code == 400
    assert r2.json().get("detail") == "Activity is full"

    # Cleanup
    activities.pop(tmp_name, None)


def test_unregister_participant():
    tmp_name = "Test Unregister"
    email = "remove_me@example.com"
    activities[tmp_name] = {
        "description": "To be removed",
        "schedule": "Soon",
        "max_participants": 5,
        "participants": [email]
    }

    # Delete existing participant
    resp = client.delete(f"/activities/{tmp_name}/participants?email={email}")
    assert resp.status_code == 200
    assert resp.json().get("message")
    assert email not in activities[tmp_name]["participants"]

    # Deleting again returns 404
    resp2 = client.delete(f"/activities/{tmp_name}/participants?email={email}")
    assert resp2.status_code == 404

    # Cleanup
    activities.pop(tmp_name, None)
*** End Patch