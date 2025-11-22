"""
reCAPTCHA Enterprise utility functions for spam protection.
"""
import logging
from typing import Optional, Union, Any

# Try to import Google Cloud reCAPTCHA Enterprise client
try:
    from google.cloud import recaptchaenterprise_v1
    from google.cloud.recaptchaenterprise_v1 import Assessment
    RECAPTCHA_ENTERPRISE_AVAILABLE = True
    AssessmentType = Assessment
except ImportError:
    RECAPTCHA_ENTERPRISE_AVAILABLE = False
    AssessmentType = Any  # Fallback type when library is not available

# Fallback to requests for standard reCAPTCHA
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_assessment(
    project_id: str, recaptcha_key: str, token: str, recaptcha_action: str, user_ip: str = None
) -> Optional[AssessmentType]:
    """Create an assessment to analyze the risk of a UI action.
    
    Args:
        project_id: Your Google Cloud Project ID.
        recaptcha_key: The reCAPTCHA key associated with the site/app
        token: The generated token obtained from the client.
        recaptcha_action: Action name corresponding to the token.
        user_ip: Optional user IP address for additional context.
        
    Returns:
        Assessment response or None if failed.
    """
    if not RECAPTCHA_ENTERPRISE_AVAILABLE:
        logger.error("Google Cloud reCAPTCHA Enterprise library not available")
        return None

    try:
        client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()

        # Set the properties of the event to be tracked.
        event = recaptchaenterprise_v1.Event()
        event.site_key = recaptcha_key
        event.token = token
        
        # Add user IP if provided
        if user_ip:
            event.user_ip_address = user_ip

        assessment = recaptchaenterprise_v1.Assessment()
        assessment.event = event

        project_name = f"projects/{project_id}"

        # Build the assessment request.
        request = recaptchaenterprise_v1.CreateAssessmentRequest()
        request.assessment = assessment
        request.parent = project_name

        response = client.create_assessment(request)

        # Check if the token is valid.
        if not response.token_properties.valid:
            logger.warning(
                "reCAPTCHA token invalid. Reasons: %s",
                response.token_properties.invalid_reason
            )
            return None

        # Check if the expected action was executed.
        if response.token_properties.action != recaptcha_action:
            logger.warning(
                "reCAPTCHA action mismatch. Expected: %s, Got: %s",
                recaptcha_action,
                response.token_properties.action
            )
            return None

        # Log the assessment results
        score = response.risk_analysis.score
        reasons = [str(reason) for reason in response.risk_analysis.reasons]
        
        logger.info(
            "reCAPTCHA assessment successful. Score: %s, Reasons: %s",
            score,
            reasons
        )

        # Get the assessment name (id) for potential annotation
        try:
            assessment_name = client.parse_assessment_path(response.name).get("assessment")
            logger.debug("Assessment ID: %s", assessment_name)
        except Exception as e:
            logger.debug("Could not parse assessment name: %s", e)

        return response

    except Exception as e:
        logger.error("reCAPTCHA Enterprise assessment failed: %s", e)
        return None


def verify_recaptcha_standard(secret_key: str, token: str, user_ip: str = None) -> dict:
    """Fallback verification using standard reCAPTCHA API.
    
    Args:
        secret_key: reCAPTCHA secret key
        token: reCAPTCHA response token
        user_ip: Optional user IP address
        
    Returns:
        Dictionary with verification results
    """
    if not REQUESTS_AVAILABLE:
        logger.error("Requests library not available for reCAPTCHA verification")
        return {'success': False, 'error': 'requests_unavailable'}

    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': secret_key,
        'response': token
    }
    
    if user_ip:
        data['remoteip'] = user_ip

    try:
        response = requests.post(verify_url, data=data, timeout=10)
        result = response.json()
        
        if result.get('success'):
            logger.info("Standard reCAPTCHA verification successful")
        else:
            logger.warning("Standard reCAPTCHA verification failed: %s", result.get('error-codes', []))
            
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error("Standard reCAPTCHA verification request failed: %s", e)
        return {'success': False, 'error': 'request_failed'}


def validate_recaptcha_token(
    project_id: str,
    public_key: str, 
    private_key: str,
    token: str,
    action: str,
    user_ip: str = None,
    required_score: float = 0.5
) -> tuple:
    """
    Validate reCAPTCHA token using Enterprise API with fallback to standard API.
    
    Args:
        project_id: Google Cloud project ID (optional for standard reCAPTCHA)
        public_key: reCAPTCHA site key
        private_key: reCAPTCHA secret key
        token: reCAPTCHA response token
        action: Expected action name
        user_ip: User's IP address
        required_score: Minimum required score (0.0-1.0)
        
    Returns:
        Tuple of (is_valid, error_message, score)
    """
    # Try Enterprise API first if project_id is provided
    if project_id and RECAPTCHA_ENTERPRISE_AVAILABLE:
        assessment = create_assessment(project_id, public_key, token, action, user_ip)
        
        if assessment:
            score = assessment.risk_analysis.score
            if score >= required_score:
                return True, "Success", score
            else:
                return False, f"Score too low: {score} < {required_score}", score
        else:
            logger.info("Enterprise API failed, falling back to standard reCAPTCHA")
    
    # Fallback to standard reCAPTCHA API
    result = verify_recaptcha_standard(private_key, token, user_ip)
    
    if result.get('success'):
        # Standard reCAPTCHA doesn't provide scores, so we assume it passes
        return True, "Success (standard)", 1.0
    else:
        error_codes = result.get('error-codes', ['unknown'])
        return False, f"Standard reCAPTCHA failed: {error_codes}", 0.0