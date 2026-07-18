# Marketplace OAuth Guide

## Features

- Authorization URL generation  
- CSRF `state` persistence + expiry + single use  
- Authorization code exchange  
- Refresh token rotation (new current token row)  
- Revocation on disconnect  
- Refresh failure → `reauth_required`  

## Security

- State bound to workspace + channel + environment + user  
- Secrets/tokens never returned in list APIs  
- Client secret encrypted  
- Generic marketplace errors without leaking secrets  
