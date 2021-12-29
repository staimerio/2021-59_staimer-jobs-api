# Retic
from retic import Router

# Controllers
import controllers.scrapper as scrapper

router = Router()

router.post("/movies/scrapper", scrapper.scrapper_movies)
router.post("/shows/scrapper", scrapper.scrapper_shows)