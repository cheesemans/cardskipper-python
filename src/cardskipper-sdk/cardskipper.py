from typing import List, Optional, Any
from pydantic import BaseModel, Field, AliasPath
from datetime import datetime, date
import xml.etree.ElementTree as ET
import requests
import xmlschema

CARDSKIPPER_API_URL = "https://api.cardskipper.se"
CARDSKIPPER_TEST_API_URL = "https://api-test.cardskipper.se"


class CardskipperMember(BaseModel):
    email: str = Field(..., validation_alias=AliasPath("ContactInfo", "@EMail"))
    first_name: str = Field(..., validation_alias="@Firstname")
    last_name: str = Field(..., validation_alias="@Lastname")


class OrganisationChildren(BaseModel):
    id: int = Field(..., validation_alias=AliasPath("@Id"))
    name: str = Field(..., validation_alias=AliasPath("@Name"))


class InformationType(BaseModel):
    id: int = Field(..., validation_alias="@Id")
    name: str = Field(..., validation_alias="@Name")
    organisation_id: int = Field(..., validation_alias="@OrganisationId")


class OrganisationUnit(BaseModel):
    id: int = Field(..., validation_alias="@Id")
    value: str = Field(..., validation_alias="@Value")
    organisation_id: int = Field(..., validation_alias="@OrganisationId")


class Role(BaseModel):
    id: int = Field(..., validation_alias="@Id")
    name: str = Field(..., validation_alias="@Name")
    description: Optional[str] = Field(default=None, validation_alias="@Description")


class Organisation(BaseModel):
    id: int = Field(..., validation_alias=AliasPath("@Id"))
    name: str = Field(..., validation_alias=AliasPath("@Name"))
    roles: List[Role] = Field(..., validation_alias=AliasPath("Roles", "Role"))
    information_types: List[InformationType] = Field(
        ..., validation_alias=AliasPath("InformationTypes", "InformationType")
    )
    children: Optional[List[OrganisationChildren]] = Field(
        default=None, validation_alias=AliasPath("Children", "CardskipperOrganisationChildren")
    )
    organisation_units: Optional[List[OrganisationUnit]] = Field(
        default=None, validation_alias=AliasPath("OrganisationUnits", "OrganisationUnit")
    )


def _convert_to_xsd(value: Any) -> str:
    match value:
        case bool():
            return str(value).lower()
        case int():
            return str(value)
        case datetime():
            return value.replace(microsecond=0).isoformat()
        case date():
            return value.isoformat()
        case _:
            return value


def _get_base_url(test_api: bool):
    if test_api:
        return CARDSKIPPER_TEST_API_URL
    return CARDSKIPPER_API_URL


def basedata_countries():
    pass


def basedata_gender():
    pass


def organisation_info(username: str, password: str, test_api: bool = False) -> List[Organisation]:
    base_url = _get_base_url(test_api)
    organisation_info_schema = xmlschema.XMLSchema(f"{base_url}/Doc/OrganisationInfo.xsd")

    response = requests.get(f"{base_url}/Organisation/Info", auth=(username, password))
    response_tree = ET.ElementTree(ET.fromstring(response.content))

    organisation_info = organisation_info_schema.to_dict(response_tree)

    organisations = [
        Organisation.model_validate(organisation) for organisation in organisation_info["Organisations"]["Organisation"]
    ]

    return organisations


def member_export(
    username: str,
    password: str,
    organisation_id: str,
    member_id: Optional[int] = None,
    role_id: Optional[int] = None,
    user_id: Optional[int] = None,
    organisation_member_id: Optional[int] = None,
    birthdate: Optional[date] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    cellphone: Optional[str] = None,
    tag_contains: Optional[str] = None,
    organisation_unit: Optional[str] = None,
    has_user_device: Optional[bool] = None,
    only_active: Optional[bool] = None,
    changed_at: Optional[datetime] = None,
    test_api: bool = False,
):  # -> CardskipperMembers:
    base_url = _get_base_url(test_api)
    search_criteria_member_schema = xmlschema.XMLSchema(f"{base_url}/Doc/SearchCriteriaMember.xsd")

    search_criteria_values = {
        "MemberId": member_id,
        "OrganisationId": organisation_id,
        "RoleId": role_id,
        "UserId": user_id,
        "OrganisationMemberId": organisation_member_id,
        "Birthdate": birthdate,
        "Firstname": first_name,
        "Lastname": last_name,
        "Cellphone": cellphone,
        "TagContains": tag_contains,
        "OrganisationUnit": organisation_unit,
        "HasUserDevice": has_user_device,
        "OnlyActive": only_active,
        "ChangedAt": changed_at,
    }

    data = ET.Element("Cardskipper")

    search_criteria = ET.SubElement(data, "SearchCriteriaMember")

    for tag, value in search_criteria_values.items():
        if value:
            ET.SubElement(search_criteria, tag).attrib = {"value": _convert_to_xsd(value)}

    if search_criteria_member_schema.is_valid(data):
        response = requests.post(f"{base_url}/Member/Export", auth=(username, password), data=ET.tostring(data))
        response_tree = ET.ElementTree(ET.fromstring(response.content))
        print(ET.dump(response_tree))

        member_schema = xmlschema.XMLSchema(f"{base_url}/Doc/MemberImport.xsd")

        member_info = member_schema.to_dict(response_tree)
        print(member_info)

    print(response.content)

    pass

    # return CardskipperMembers.model_validate(xmltodict.parse(response.content))
