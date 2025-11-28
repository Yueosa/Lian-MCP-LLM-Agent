from .BaseModel import RelationalModel

def auto_initialize_models():
    """自动发现并初始化所有 RelationalModel 的子类"""
    models = RelationalModel.__subclasses__()
    
    for model in models:
        model.model_rebuild()
        model._extract_relationships_from_fields()
