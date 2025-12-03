from .BaseModel import RelationalModel


def auto_initialize_models():
    """自动发现并初始化所有 RelationalModel 的子类"""
    models = RelationalModel.__subclasses__()
    
    types_namespace = {model.__name__: model for model in models}
    
    for model in models:
        model.model_rebuild(_types_namespace=types_namespace)
        model._extract_relationships_from_fields()
