from fastapi import APIRouter, Depends, status, UploadFile, File
from typing import List
from dependency_injector.wiring import inject, Provide

from app.crosscutting.authorization import getAuthenticatedUser, authorizeRoles
from app.schemas.request.medic_create_request import MedicCreateRequest
from app.schemas.request.medic_update_request import MedicUpdateRequest
from app.schemas.response.medic_response import MedicResponse
from app.security.domain.model.user import Role, User
from app.service.medic_service import MedicService
from app.core.container import Container
from uuid import uuid4
import os

router = APIRouter(
    prefix="/api/v1/medics",
    tags=["Medics"]
)

# Listar todos los médicos habilitados
@router.get("/", response_model=List[MedicResponse],
                description="Retorna una lista de todos los médicos habilitados en el sistema. No requiere autenticación.")
@inject
def get_all_medics(
    medic_service: MedicService = Depends(Provide[Container.medicService])
):
    return medic_service.list_all()

# Filtrar por especialidad (parámetro en la URL)
@router.get("/specialty/{specialty}", response_model=List[MedicResponse],
             description="Filtra y devuelve una lista de médicos por especialidad. Búsqueda insensible a mayúsculas.")
@inject
def get_medics_by_specialty(
    specialty: str,
    medic_service: MedicService = Depends(Provide[Container.medicService])
):
    return medic_service.list_by_specialty(specialty)

# Filtrar por nombre (parámetro en la URL)
@router.get("/name/{name}", response_model=List[MedicResponse],
            description="Filtra y devuelve una lista de médicos por nombre. Búsqueda parcial e insensible a mayúsculas.")
@inject
def get_medics_by_name(
    name: str,
    medic_service: MedicService = Depends(Provide[Container.medicService])
):
    return medic_service.list_by_name(name)

# Registrar perfil del médico (requiere login como MEDIC)
@router.post(
    "/register-profile",
    response_model=MedicResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authorizeRoles([Role.MEDIC]))],
    description="Permite a un médico autenticado registrar su perfil profesional (especialidad, experiencia, etc.)."
)
@inject
def register_medic_profile(
    data: MedicCreateRequest,
    current_user: User = Depends(getAuthenticatedUser),
    service: MedicService = Depends(Provide[Container.medicService])
):
    return service.create_profile_for_medic(current_user.id, data)

UPLOAD_DIR = "static/profile_pictures"

@router.post("/upload-photo", response_model=str, status_code=200,
             description="Permite al médico autenticado subir una foto de perfil. La URL devuelta puede ser usada públicamente.")
@inject
def upload_medic_photo(
    current_user: User = Depends(getAuthenticatedUser),
    file: UploadFile = File(...),
    service: MedicService = Depends(Provide[Container.medicService])
):
    # Asegurar carpeta
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generar nombre único
    filename = f"{uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Guardar archivo
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Guardar nombre en BD (solo el filename, no la URL completa)
    service.update_profile_picture(current_user.id, filename)

    # Retornar URL accesible
    return f"/static/profile_pictures/{filename}"



@router.patch(
    "/update-profile",
    response_model=MedicResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(authorizeRoles([Role.MEDIC]))],
    description="Permite al médico actualizar su perfil profesional. Solo se actualizan los campos enviados."
)
@inject
def update_medic_profile(
    data: MedicUpdateRequest,
    current_user: User = Depends(getAuthenticatedUser),
    service: MedicService = Depends(Provide[Container.medicService])
):
    return service.update_profile_for_medic(current_user.id, data)


