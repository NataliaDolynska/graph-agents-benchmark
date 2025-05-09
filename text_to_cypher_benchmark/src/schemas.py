
class EntitySchema(BaseModel):
    label: str
    description: Optional[str] = None
    properties: dict[str, DataType]


class RelationSchema(BaseModel):
    label: str
    subj_label: str
    obj_label: str
    properties: dict[str, DataType]


class PropertyGraphSchema(BaseModel):
    name: str
    entities: list[EntitySchema]
    relations: list[RelationSchema]

    def to_json(self, exclude_description=False):
        res = self.model_dump(mode='json')
        if exclude_description:
            for ent in res['entities']:
                ent.pop('description')
        return res

    def to_str(self, exclude_description=False):
        return json.dumps(self.to_json(exclude_description), indent=2)

    def to_sorted(self) -> 'PropertyGraphSchema':
        schema = copy.deepcopy(self)
        schema.entities = sorted(schema.entities, key=lambda x: x.label)
        schema.relations = sorted(schema.relations, key=lambda x: (x.label, x.subj_label, x.obj_label))
        for x in schema.entities + schema.relations:
            x.properties = dict(sorted(x.properties.items()))
        return PropertyGraphSchema(**schema.model_dump(mode='json'))

    @classmethod
    def from_json(cls, data, add_meta_properties={'name': DataType.STR}):
        schema = cls(**data)
        for ent in schema.entities:
            if add_meta_properties:
                ent.properties = dict(**add_meta_properties, **ent.properties)
        schema = cls(**schema.model_dump(mode='json'))  # Validate again
        return schema


def deduplicate(input_list):
    seen = set()
    return [x for x in input_list if not (x in seen or seen.add(x))]

