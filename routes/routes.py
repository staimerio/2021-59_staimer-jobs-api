# Retic
from retic import Router

# Controllers
import controllers.espapelis as espapelis

router = Router()

router.post("/espapelis/movies", espapelis.scrapper_espapelis_movies)