# services/__init__.py 파일에 내용을 넣으면?

print("서비스 패키지가 로딩되었습니다!") # 1. import 할 때 이 문장이 자동 출력됨

# 2. 복잡한 경로를 단순하게 줄여줌 (Shortcut)
# from .market_data import get_market_pulse 

# 이렇게 해두면 외부에서는
# from services.market_data import get_market_pulse (길게 안 쓰고)
# from services import get_market_pulse (짧게 쓸 수 있음!)