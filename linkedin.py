import requests
from django.conf import settings

def post_job_to_linkedin(job_details):
    access_token = settings.LINKEDIN_ACCESS_TOKEN  # Store token in Django settings for security
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # Fetch the LinkedIn user sub (optional, but recommended to get the user identifier)
    response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        linkedin_sub = user_data.get("sub", "")  # Get the LinkedIn user sub (unique identifier)
        if not linkedin_sub:
            return {"error": "LinkedIn Sub not found."}

        # Prepare the LinkedIn post payload
        payload = {
            "author": f"urn:li:person:{linkedin_sub}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": f"Exciting job opportunity: {job_details['role']} at {job_details['job_company_name']}!\n\n{job_details['job_description']}\nLocation: {job_details['location']}"
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # Post the job details to LinkedIn
        linkedin_api_url = "https://api.linkedin.com/v2/ugcPosts"
        response = requests.post(linkedin_api_url, headers=headers, json=payload)

        if response.status_code == 201:
            return {"success": "Job posted successfully to LinkedIn.", "response": response.json()}
        else:
            return {"error": f"Failed to post job details to LinkedIn: {response.status_code} - {response.text}"}
    else:
        return {"error": f"Failed to fetch user info: {response.status_code} - {response.text}"}
