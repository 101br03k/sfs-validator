from pydantic import BaseModel, HttpUrl, Field, field_validator, model_validator, ValidationInfo
from typing import Optional, List, Dict, Union, Literal
from ruamel.yaml import YAML
from pathlib import Path
import sys
import webbrowser

yaml = YAML()

# ------------------------------------------------------
# MAPPINGS: Friendly descriptions and direct doc links
# ------------------------------------------------------

# ------------------------------------------------------
# config.yaml
# ------------------------------------------------------
FIELD_HELP = {
    'general.appUrl': {
        'desc': 'Base URL where the app is hosted.',
        'doc': 'main-configuration'
    },
    'general.athlete.birthday': {
        'desc': 'Your birthday in YYYY-MM-DD format.',
        'doc': 'main-configuration'
    },
    'general.athlete.maxHeartRateFormula': {
        'desc': 'Method or override for max heart rate.',
        'doc': 'main-configuration?id=athlete-heart-rate-zones'
    },
    'general.athlete.weightHistory': {
        'desc': 'Map of dates to weight values (int/float).',
        'doc': 'main-configuration?id=athlete-weight-history'
    },
    'appearance.locale': {
        'desc': 'UI language of the app.',
        'doc': 'main-configuration'
    },
    'import.numberOfNewActivitiesToProcessPerImport': {
        'desc': 'Max number of new activities to fetch.',
        'doc': 'main-configuration'
    },
    'metrics.eddington': {
        'desc': 'Custom Eddington score tabs.',
        'doc': 'main-configuration'
    },
    'integrations.ai.provider': {
        'desc': 'Which AI service to use',
        'doc': 'ai-integration'
    },

# ------------------------------------------------------
# custom-gear.yaml
# ------------------------------------------------------

    'custom-gear.name': {
        'desc': 'Custom name to display for this gear item.',
        'doc': 'custom-gear'
    },
    'custom-gear.stravaGearId': {
        'desc': 'The Strava gear ID this entry links to.',
        'doc': 'custom-gear'
    },
    'custom-gear.weight': {
        'desc': 'Weight in kilograms (optional).',
        'doc': 'custom-gear'
    },
    'custom-gear.default': {
        'desc': 'Marks this gear item as the default selection.',
        'doc': 'custom-gear'
    },
# ------------------------------------------------------
# gear-maintenance.yaml
# ------------------------------------------------------
    'gear-maintenance.stravaGearId': {
        'desc': 'The Strava gear ID to which maintenance applies.',
        'doc': 'gear-maintenance'
    },
    'gear-maintenance.maintenanceDistance': {
        'desc': 'Distance threshold (in km) after which maintenance is due.',
        'doc': 'gear-maintenance'
    },
    'gear-maintenance.resetDistance': {
        'desc': 'Optional distance to reset the maintenance counter.',
        'doc': 'gear-maintenance'
    },
}

DOC_BASE_URL = "https://statistics-for-strava-docs.robiningelbrecht.be/#/configuration/"


# ------------------------------------------------------
# SCHEMA MODELS
# ------------------------------------------------------

# --- config.yaml models ---
Locale = Literal['en_US', 'fr_FR', 'it_IT', 'nl_BE', 'de_DE', 'pt_BR', 'pt_PT', 'zh_CN']
UnitSystem = Literal['metric', 'imperial']
TimeFormat = Literal[12, 24]
Visibility = Literal['everyone', 'followers_only', 'only_me']
HeartRateMode = Literal['relative', 'absolute']
AIProvider = Literal['anthropic', 'gemini', 'ollama', 'openAI', 'deepseek', 'mistral']

class Zone(BaseModel):
    from_: int = Field(..., alias='from')
    to: Optional[int]

    class Config:
        extra = "forbid"

class HeartRateZones(BaseModel):
    mode: HeartRateMode
    default: Dict[str, Zone]

    class Config:
        extra = "forbid"

class Athlete(BaseModel):
    birthday: str
    maxHeartRateFormula: Union[str, Dict[str, int]]
    heartRateZones: HeartRateZones
    weightHistory: Dict[str, Union[int, float]]
    ftpHistory: List[int]

    class Config:
        extra = "forbid"

class General(BaseModel):
    appUrl: HttpUrl
    appSubTitle: Optional[str]
    profilePictureUrl: Optional[str]
    ntfyUrl: Optional[str]
    athlete: Athlete

    class Config:
        extra = "forbid"

class DateFormat(BaseModel):
    short: str
    normal: str

    class Config:
        extra = "forbid"

class Appearance(BaseModel):
    locale: Locale
    unitSystem: UnitSystem
    timeFormat: TimeFormat
    dateFormat: DateFormat
    sportTypesSortingOrder: List[str]

    class Config:
        extra = "forbid"

class ImportSettings(BaseModel):
    numberOfNewActivitiesToProcessPerImport: int
    sportTypesToImport: List[str]
    activityVisibilitiesToImport: List[Visibility]
    skipActivitiesRecordedBefore: Optional[str]
    activitiesToSkipDuringImport: List[str]

    class Config:
        extra = "forbid"

class EddingtonEntry(BaseModel):
    label: str
    showInNavBar: bool
    sportTypesToInclude: List[str]

    class Config:
        extra = "forbid"

class Metrics(BaseModel):
    eddington: List[EddingtonEntry]
    consistencyChallenges: List

    class Config:
        extra = "forbid"

class Zwift(BaseModel):
    level: Optional[int]
    racingScore: Optional[int]

    class Config:
        extra = "forbid"

class AIConfiguration(BaseModel):
    key: str
    model: str
    url: Optional[str]

    class Config:
        extra = "forbid"

class AIIntegration(BaseModel):
    enabled: bool
    enableUI: bool
    provider: Optional[AIProvider] = None
    configuration: Optional[AIConfiguration] = None

    @model_validator(mode='before')
    def skip_nested_if_disabled(cls, values):
        if not values.get('enabled', False):
            values.pop('provider', None)
            values.pop('configuration', None)
        return values

    @model_validator(mode='after')
    def check_required_if_enabled(cls, values):
        if values.enabled:
            if values.provider is None:
                raise ValueError('provider is required when AI integration is enabled')
            if values.configuration is None:
                raise ValueError('configuration is required when AI integration is enabled')
        return values

    class Config:
        extra = "forbid"

class Integrations(BaseModel):
    ai: AIIntegration

    class Config:
        extra = "forbid"

class ConfigModel(BaseModel):
    general: General
    appearance: Appearance
    import_: ImportSettings = Field(..., alias='import')
    metrics: Metrics
    zwift: Zwift
    integrations: Integrations

    class Config:
        extra = "forbid"

# --- custom-gear.yaml models ---
class CustomGearEntry(BaseModel):
    tag: str
    label: str
    isRetired: bool

    class Config:
        extra = "forbid"

class CustomGearModel(BaseModel):
    enabled: bool
    hashtagPrefix: str
    customGears: List[CustomGearEntry]

    @model_validator(mode='before')
    def skip_nested_if_disabled(cls, values):
        if not values.get('enabled', False):
            values.pop('hashtagPrefix', None)
            values.pop('customGears', None)
        return values

    @model_validator(mode='after')
    def check_required_if_enabled(cls, values):
        if values.enabled:
            if getattr(values, "hashtagPrefix", None) is None:
                raise ValueError('hashtagPrefix is required when custom gear is enabled')
            if getattr(values, "customGears", None) is None:
                raise ValueError('customGears is required when custom gear is enabled')
        return values

    class Config:
        extra = "forbid"

# --- gear-maintenance.yaml models ---
class MaintenanceInterval(BaseModel):
    value: int
    unit: str  # e.g. 'km', 'mi', 'hours', 'days'

    class Config:
        extra = "forbid"

class MaintenanceTask(BaseModel):
    tag: str
    label: str
    interval: MaintenanceInterval

    class Config:
        extra = "forbid"

class Component(BaseModel):
    tag: str
    label: str
    imgSrc: Optional[str]
    attachedTo: List[str]
    maintenance: List[MaintenanceTask]

    class Config:
        extra = "forbid"

class GearImage(BaseModel):
    gearId: str
    imgSrc: Optional[str]

    class Config:
        extra = "forbid"

class GearMaintenanceModel(BaseModel):
    enabled: bool
    hashtagPrefix: str
    components: List[Component]
    gears: List[GearImage]

    class Config:
        extra = "forbid"


# ------------------------------------------------------
# Error Display
# ------------------------------------------------------


def get_value_by_path(data, path):
    """Retrieve nested value in dict/list using a list of keys/indexes."""
    for key in path:
        if isinstance(data, dict) and key in data:
            data = data[key]
        elif isinstance(data, list) and isinstance(key, int) and 0 <= key < len(data):
            data = data[key]
        else:
            return "<value not found>"
    return data

def print_friendly_errors(errors: list, original_data: dict, auto_open_docs: bool = False):
    printed_links = set()
    print("❌ Validation failed:\n")

    for err in errors:
        loc_path = list(err['loc'])
        loc_str = ".".join(str(p) for p in loc_path)
        msg = err['msg']
        field_info = FIELD_HELP.get(loc_str)
        expected = f"Expected type: {err.get('type', 'unknown')}"

        # Get the actual invalid value from original data
        invalid_value = get_value_by_path(original_data, loc_path)

        print(f"• ❌ `{loc_str}`: {msg}")
        print(f"  🔎 Invalid value: {invalid_value}")

        if field_info:
            print(f"  🧾 {field_info['desc']}")
            doc_url = f"{DOC_BASE_URL}{field_info['doc']}"
            print(f"  📘 See docs: {doc_url}")
            if auto_open_docs and doc_url not in printed_links:
                webbrowser.open(doc_url)
                printed_links.add(doc_url)
        else:
            print(f"  ↪️  {expected}")
            print(f"  📘 Docs: {DOC_BASE_URL}")

        print()  # Line break


# ------------------------------------------------------
# YAML + Validation Runner config.yaml
# ------------------------------------------------------

def validate_yaml_config(file_path: str, model_class, open_docs: bool = False):
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    with path.open('r', encoding='utf-8') as f:
        data = yaml.load(f)

    try:
        model_class.model_validate(data)
        print(f"✅ {file_path} is valid!")
    except Exception as e:
        print(f"❌ {file_path} has errors!")
        if hasattr(e, "errors"):
            print_friendly_errors(e.errors(), data, auto_open_docs=open_docs)
        else:
            print(str(e))
        sys.exit(1)

# ------------------------------------------------------
# Entry Point
# ------------------------------------------------------

if __name__ == '__main__':
    validate_yaml_config("config.yaml", ConfigModel, open_docs=False)
    validate_yaml_config("custom-gear.yaml", CustomGearModel, open_docs=False)
    validate_yaml_config("gear-maintenance.yaml", GearMaintenanceModel, open_docs=False)
