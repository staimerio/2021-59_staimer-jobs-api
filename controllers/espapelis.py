# Retic
from retic import Request, Response, Next, App as app

# Services
from retic.services.responses import success_response
from services.movies import espapelis


def scrapper_espapelis_movies(req: Request, res: Response, next: Next):
    """Get all novel from latests page"""
    _result = espapelis.scrapper_espapelis_movies()
    """Check if exist an error"""
    if _result['valid'] is False:
        return res.bad_request(_result)
    """Response the data to client"""
    res.ok(_result)
