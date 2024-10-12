import fastapi
from src.api.routes.admin import router as admin_router
from src.api.routes.appointment import router as appointment_router
from src.api.routes.chat import router as chat_router
from src.api.routes.prescription import router as prescription_router
from src.api.routes.reminder import router as reminder_router
from src.api.routes.timeslot import router as timeslot_router
from src.api.routes.user import router as user_router

router = fastapi.APIRouter()
router.include_router(router=user_router)
router.include_router(router=timeslot_router)
router.include_router(router=appointment_router)
router.include_router(router=prescription_router)
router.include_router(router=chat_router)
router.include_router(router=admin_router)
router.include_router(router=reminder_router)
