# Retic
from retic import Request, Response, Next, App as app
from retic.services.validations import validate_obligate_fields

# Services
from retic.services.responses import error_response, success_response
from services.movies import scrapper


def scrapper_movies(req: Request, res: Response, next: Next):
    """Validate obligate params"""
    _validate = validate_obligate_fields({
        u'wp_login': req.param('wp_login'),
        u'wp_admin': req.param('wp_admin'),
        u'wp_username': req.param('wp_username'),
        u'wp_password': req.param('wp_password'),
        u'wp_url': req.param('wp_url'),
    })

    """Check if has errors return a error response"""
    if _validate["valid"] is False:
        return res.bad_request(
            error_response(
                "The param {} is necesary.".format(_validate["error"])
            )
        )

    """Get all novel from latests page"""
    _result = scrapper.scrapper_movies(
        req.param('wp_login'),
        req.param('wp_admin'),
        req.param('wp_username'),
        req.param('wp_password'),
        req.param('wp_url'),
        req.param('origin', "pelisplushd"),
        req.param('page', 1),
    )
    """Check if exist an error"""
    if _result['valid'] is False:
        return res.bad_request(_result)
    """Response the data to client"""
    res.ok(_result)


def scrapper_shows(req: Request, res: Response, next: Next):
    """Validate obligate params"""
    _validate = validate_obligate_fields({
        u'wp_url': req.param('wp_url'),
    })

    """Check if has errors return a error response"""
    if _validate["valid"] is False:
        return res.bad_request(
            error_response(
                "The param {} is necesary.".format(_validate["error"])
            )
        )

    """Get all novel from latests page"""
    _result = scrapper.scrapper_shows(
        req.param('wp_url'),
        req.param('page', 1),
    )
    """Check if exist an error"""
    if _result['valid'] is False:
        return res.bad_request(_result)
    """Response the data to client"""
    res.ok(_result)
