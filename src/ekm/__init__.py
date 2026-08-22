"""Engineering Knowledge Model (EKM) runtime."""

from ekm.aerf_writeback import (
    AERFWritebackFieldPlan,
    AERFWritebackPlan,
    apply_aerf_writeback,
    plan_aerf_writeback,
    write_aerf_stages_to_ekm,
)
from ekm.field_registry import FieldEditorSpec, get_field_editor_spec
from ekm.errors import EKMError, EKMIOError, EKMValidationError, EKMVersionError
from ekm.io import document_summary, init_empty, load, load_json_file, save
from ekm.model import EKMDocument, SUPPORTED_SCHEMA_VERSION
from ekm.paths import EKM_DIR_NAME, EKM_FILENAME, ekm_path_for_project, resolve_ekm_path
from ekm.prompt_context import (
    EKMPromptBundle,
    extract_ekm_family_id,
    load_ekm_prompt_bundle,
    load_ekm_sections_for_prompt,
)
from ekm.validate import assert_supported_version, validate_document, validate_document_data
from ekm.view_model import EKMViewModel, FieldView, SearchHit, SectionView

__all__ = [
    "AERFWritebackFieldPlan",
    "AERFWritebackPlan",
    "EKM_DIR_NAME",
    "EKM_FILENAME",
    "EKMDocument",
    "EKMPromptBundle",
    "EKMError",
    "EKMIOError",
    "EKMValidationError",
    "EKMVersionError",
    "EKMViewModel",
    "FieldEditorSpec",
    "FieldView",
    "SearchHit",
    "SectionView",
    "SUPPORTED_SCHEMA_VERSION",
    "apply_aerf_writeback",
    "assert_supported_version",
    "document_summary",
    "ekm_path_for_project",
    "extract_ekm_family_id",
    "get_field_editor_spec",
    "init_empty",
    "load",
    "load_json_file",
    "load_ekm_prompt_bundle",
    "load_ekm_sections_for_prompt",
    "plan_aerf_writeback",
    "resolve_ekm_path",
    "save",
    "validate_document",
    "validate_document_data",
    "write_aerf_stages_to_ekm",
]
