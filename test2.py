import requests

def get_organization_urn(access_token, company_name):
    """
    Fetch the organization URN for a company by its name.
    """
    url = "https://api.linkedin.com/v2/organizations"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "q": "vanityName",  # or use "universalName" if vanityName doesn't work
        "vanityName": company_name  # Replace with your company name
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if "elements" in data and len(data["elements"]) > 0:
            organization = data["elements"][0]
            return organization.get("organization", "Organization URN not found")
        else:
            return "Organization not found"
    else:
        return f"Error: {response.status_code}, {response.json()}"

# Example usage
access_token = "AQXLVBHVBRscBgb9pbrwqqmWkG3bQaoIuk5rzknbWOHUtTjUpQokF5U-VY_0A2ZGPe1ihyDnd13JC-bi8_xfQrhmVz4qImZjjvkEI3zB_LkojdoRw19cORZHphuzZl6pWHQVpryKy2ZXCE2-BsjGkQO1WUCkGkBNLo2pMIrqPfdUm0kjTu1HhW2PTXqt1GVi85LPUqLFUbI5FMICjmPt90Ekkcm6QsPvmwLk_eoENn_rqD2sZaX7xhdP7rPQZewoXveTQs9_laqTg3uViuTfSzbNwGf0dZXHrH5HnKduG750y10k51PuAJooCdMKHvMuKo_gTuiwgOGVo5RE4NfbH54oWOh9Bg"  # Replace with your actual token
company_name = "testnewcompany123"
urn = get_organization_urn(access_token, company_name)
print(f"Organization URN: {urn}")
