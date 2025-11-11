import math
import re

class MathTools:
    async def calculate_expression(self, expression: str) -> float:
        """计算数学表达式"""
        try:
            # 安全检查：只允许数学表达式
            safe_pattern = r'^[0-9+\-*/().\s]+$'
            if not re.match(safe_pattern, expression):
                return "错误: 表达式包含不安全字符"
            
            # 使用eval计算表达式（在生产环境中应该使用更安全的方法）
            result = eval(expression, {"__builtins__": None}, {
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "sqrt": math.sqrt, "log": math.log, "exp": math.exp,
                "pi": math.pi, "e": math.e
            })
            return float(result)
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    async def convert_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """单位转换"""
        conversions = {
            "length": {
                "m_km": 0.001, "km_m": 1000,
                "m_cm": 100, "cm_m": 0.01,
                "in_cm": 2.54, "cm_in": 0.393701
            },
            "weight": {
                "kg_g": 1000, "g_kg": 0.001,
                "kg_lb": 2.20462, "lb_kg": 0.453592
            }
        }
        
        try:
            key = f"{from_unit}_{to_unit}"
            for category in conversions.values():
                if key in category:
                    return value * category[key]
            return f"不支持的单位转换: {from_unit} -> {to_unit}"
        except Exception as e:
            return f"单位转换错误: {str(e)}"
