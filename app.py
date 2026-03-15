import streamlit as st
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# 시나리오 공개 데이터 (UI 표시용)
# ETHOS_시나리오_최종본_v2.md 기반
# ─────────────────────────────────────────────
SCENARIO_PUBLIC = {
    "scenario_01": {
        "title": "정보보호",
        "persona_name": "이현도",
        "persona_role": "사수 (시니어 개발자 3년차)",
        "persona_intro": "어젯밤 야근으로 기능을 끝낸 걸 내심 뿌듯해하는 사수. 팀에서 실력으로 인정받아온 만큼 자기 판단을 쉽게 굽히지 않는다. 후배가 진심으로 걱정해주는 건 알아채지만, 틀렸다고 몰아붙이는 순간 선임 자존심이 올라온다.",
        "persona_attitude": '"그 정도 판단은 내가 할 수 있어. 약관도 읽어봤고, 3년 동안 이렇게 해왔는데 문제 생긴 적 없잖아."',
        "hint_main": "논리보다 먼저 어젯밤 야근을 알아줘 보세요.",
        "situation": "오전 10시 40분. 20분 뒤면 팀 전체 주간 회의가 잡혀 있다.\n\n당신이 코드 리뷰를 마치고 슬랙을 열었을 때, 사수 이현도의 DM이 와 있다.\n\n**이현도 (10:23):** \"야, 나 어젯밤에 이 기능 겨우 끝냈다. ChatGPT한테 우리 DB 스키마랑 API 키 통째로 붙여넣고 코드 짜달라고 했어. 어차피 ChatGPT는 입력 데이터 학습 안 한다고 약관에 나와 있잖아. 너도 막히면 이렇게 써봐, 엄청 빠르거든.\" \"오늘 회의 때 데모 보여줄 수 있을 것 같아 👍\"\n\n회의까지 20분. 이현도는 지금 자기 자리에 앉아서 발표 자료를 다듬고 있다.",
        "initial_message": "야, 나 어젯밤에 이 기능 겨우 끝냈다. ChatGPT한테 우리 DB 스키마랑 API 키 통째로 붙여넣고 코드 짜달라고 했어. 어차피 ChatGPT는 입력 데이터 학습 안 한다고 약관에 나와 있잖아. 너도 막히면 이렇게 써봐, 엄청 빠르거든. 오늘 회의 때 데모 보여줄 수 있을 것 같아 👍",
        "hints": {
            "T1": "대형 IT 기업 중에 사내 AI 도구 사용을 아예 전면 금지한 곳이 있어요. 왜 그런 결정을 내렸을지 이현도에게 물어보세요.",
            "T2": "만약 당신이 이 API 키를 손에 넣은 외부인이라면, 지금 이 순간 무엇을 할 수 있을까요? 그 시나리오를 이현도에게 직접 말해보세요.",
            "T3": "이현도가 가장 두려워하는 건 보안 원칙이 아니에요. '내가 직접 책임을 지는 상황'이에요. API 키 유출이 이현도 본인에게 어떤 결과를 가져올 수 있는지 구체적으로 짚어보세요.",
            "T3.5": "이현도는 지금 '이미 늦었다'고 느끼고 있어요. 하지만 지금 당장 할 수 있는 행동이 하나 있어요. 그게 뭔지 먼저 제안해보세요.",
        },
        "ethics_point": "외부 AI 서비스에 사내 민감 데이터·API 키를 입력하는 것은 데이터 보안 사고의 직접적 원인입니다. 약관의 '학습 미사용' 조항은 전송 자체를 막지 않으며, 서버 로그 및 보안 사고 위험은 여전히 존재합니다.",
        "kisdi": "⑨ 안전성 원칙 — AI 활용 시 데이터 보안 및 접근 권한 관리 의무",
        "debrief_good": "야근을 먼저 인정해준 경우 / API 키의 실시간 위험성을 구체적으로 그린 경우 / 재발급이라는 현실적 대안을 제시한 경우",
        "debrief_bad": "'그거 보안 위반이에요'처럼 단정 짓고 시작한 경우 → 이현도의 체면을 건드려 대화가 닫혔을 수 있어요",
        "debrief_key": "'약관의 학습 미사용'과 '외부 서버 전송 자체'는 다른 문제라는 점이 T1→T2의 핵심이에요.",
    },
    "scenario_02": {
        "title": "AI 편향",
        "persona_name": "박서연",
        "persona_role": "PM (기획팀 2년차)",
        "persona_intro": "데모 성공에 이번 인사고과가 걸려 있다는 걸 누구보다 잘 안다. 찜찜한 구석이 없는 건 아니지만 지금은 일단 넘어가고 싶은 상태. '네 잘못이다' 식으로 몰아붙이면 즉각 닫히지만, 같이 해결책을 찾아주는 사람에게는 마음을 연다.",
        "persona_attitude": '"저도 걱정이 없는 건 아닌데, 지금 당장 제가 할 수 있는 게 없잖아요."',
        "hint_main": "박서연이 찜찜하게 느끼는 부분을 먼저 알아줘 보세요.",
        "situation": "오후 7시 20분. 사무실 불이 하나둘 꺼지고 있다.\n\n투자자 데모가 2주 후로 잡혀 있다. 당신이 노트북을 챙기다 옆 자리 모니터를 보니, 혼자 야근 중인 PM 박서연의 화면에 데모 준비 일정표가 열려 있다. 눈에 띄는 건 하나 — 편향 테스트 항목이 아예 빠져 있다.\n\n박서연이 눈치채고 먼저 말한다.\n\n**박서연 (7:22):** \"아, 봤어요? 편향 테스트요. 저도 넣으려고 했는데 일정이 진짜 안 맞아요. 데모가 2주 후잖아요. 어차피 최종 합격 결정은 HR이 하는 거고, 87% 정확도면 일단 보여주기엔 충분하지 않나요?\"\n\n찜찜한 게 없는 건 아닌 것 같다. 하지만 일정 압박이 더 크게 느껴지는 표정이다.",
        "initial_message": "아, 봤어요? 편향 테스트요. 저도 넣으려고 했는데 일정이 진짜 안 맞아요. 데모가 2주 후잖아요. 어차피 최종 합격 결정은 HR이 하는 거고, 87% 정확도면 일단 보여주기엔 충분하지 않나요?",
        "hints": {
            "T1": "채용 AI가 아무리 정확해도, 특정 그룹에게만 불리하게 작동하면 정확도 숫자는 의미가 없어요. 박서연이 진짜 두려워하는 건 윤리 문제가 아니라 데모 리스크예요. 그 언어로 접근해보세요.",
            "T2": "만약 당신이 투자자라면, 데모 도중 채용 AI가 특정 그룹 지원자를 낮게 평가한다는 걸 발견했을 때 어떤 반응을 보일까요? 그 시나리오를 박서연에게 직접 말해보세요.",
            "T3": "박서연은 지금 방법을 몰라서 못 움직이는 거예요. '네가 잘못했다'가 아니라 '편향 테스트를 데모 강점으로 만들 수 있다'는 구체적인 그림을 같이 그려보세요.",
            "T3.5": "박서연은 투자자 앞에서 편향 질문을 받는 상황이 가장 두려워요. 그 장면을 구체적으로 그려서 말해보세요. 그리고 그걸 막을 수 있는 방법도 같이 제시해보세요.",
        },
        "ethics_point": "87% 정확도와 공정성은 별개 지표입니다. 채용처럼 누군가의 인생에 영향을 미치는 고위험 AI는 출시 전 편향 감사(Bias Audit)가 필수입니다. '사람이 최종 결정한다'는 자동화 편향을 막지 못합니다.",
        "kisdi": "③ 다양성 존중 · ⑧ 책임성 — 고위험 AI 시스템의 사전 편향 검증 및 차별 방지 의무",
        "debrief_good": "박서연이 찜찜해하는 걸 먼저 알아줬을 때 / 편향 테스트를 데모 강점으로 프레이밍했을 때 / 구체적인 일정 대안을 같이 제시했을 때",
        "debrief_bad": "'편향 테스트는 필수예요'처럼 원칙만 반복한 경우 → 박서연은 방법이 필요한 상태였어요",
        "debrief_key": "87% 정확도와 공정성은 별개 지표라는 점, 그리고 '사람이 최종 결정한다'가 자동화 편향을 막지 못한다는 점이 핵심이에요.",
    },
    "scenario_03": {
        "title": "AI 프라이버시",
        "persona_name": "김민석",
        "persona_role": "ML 파트 리드 (4년차)",
        "persona_intro": "이번 스프린트에서 팀 최대 성과를 낸 게 내심 뿌듯한 선임. 모델 성능으로는 팀에서 손꼽히고, 기술 판단에 자부심이 있다. 이름이랑 전화번호를 지우면 비식별화 완료라고 진심으로 믿는다.",
        "persona_attitude": '"이름·전화번호 다 뺐는데 뭐가 문제예요? 그러면 누가 누군지 어떻게 알아요?"',
        "hint_main": "18% 성과를 부정하면 바로 닫혀요. '그 성과를 내일 리뷰에서 문제 없이 발표하려면'이라는 방향이 더 잘 통해요.",
        "situation": "오후 4시 50분. 내일 오전 스프린트 리뷰가 잡혀 있다.\n\n팀 컨플루언스에 김민석이 올려둔 리뷰 준비 문서를 열었다. 이번 스프린트 성과 정리 항목에 이런 내용이 있다.\n\n**모델 성능 개선 — 김민석:** \"고객 건강 데이터 50만 건 파인튜닝 적용. 이름·전화번호 제거 후 학습 진행. 정확도 18%p 향상.\" \"비식별 처리 완료. 내일 리뷰 때 발표 예정.\"\n\n잠깐 멈췄다. '비식별 처리 완료'라는 한 줄이 마음에 걸린다. 김민석은 자리에 있다.",
        "initial_message": "어, 문서 봤어요? 고객 건강 데이터 50만 건 파인튜닝했거든요. 이름·전화번호 다 뺐으니까 비식별 처리 완료된 거잖아요. 이번 스프린트 18%p 향상이면 팀 전체 최대 성과인데, 내일 발표 기대돼요.",
        "hints": {
            "T1": "이름과 전화번호를 지운 데이터를 '비식별화 완료'로 보는 경우가 많아요. 하지만 개인정보보호법이 요구하는 기준은 여기서 훨씬 엄격해요. 왜 그 기준이 다른지 김민석에게 물어보세요.",
            "T2": "만약 당신이 이 데이터셋을 검토하는 외부 개인정보보호 감사관이라면, 나이·지역·건강 키워드가 조합된 50만 건을 보고 어떤 질문을 먼저 던질까요? 그 시나리오를 김민석에게 직접 말해보세요.",
            "T3": "서비스 가입 약관의 포괄 동의와, AI 학습 목적으로 건강 데이터를 사용하겠다는 명시적 동의는 법적으로 구분돼요. 김민석이 약관으로 커버된다고 생각한다면 그 차이를 짚어보세요.",
            "T3.5": "김민석은 지금 '내일 발표를 어떻게 수습하냐'가 제일 두려운 거예요. 성과 수치는 그대로 발표하면서 리스크만 차단할 수 있는 방법을 먼저 제안해보세요.",
        },
        "ethics_point": "이름·전화번호 제거는 법적 비식별화의 충분 조건이 아닙니다. 나이·지역·건강 이력의 조합은 개인 재식별을 가능하게 하며, 건강정보는 개인정보보호법상 민감정보로 AI 학습 목적 사용에는 별도 명시적 동의가 필요합니다.",
        "kisdi": "⑤ 프라이버시 보호 원칙 — AI 학습 데이터의 적법한 수집·처리 및 민감정보 별도 동의 의무",
        "debrief_good": "18%p 성과를 먼저 인정하고 시작한 경우 / 재식별 원리를 구체적 예시로 설명한 경우 / 방법론 보류+수치 발표라는 대안을 제시한 경우",
        "debrief_bad": "'개인정보보호법 위반이에요'처럼 단정 짓고 시작한 경우 → 성과에 자부심이 있는 선임의 방어심을 건드렸을 수 있어요",
        "debrief_key": "'이름·번호 제거 = 비식별화 완료'가 왜 틀렸는지 — 나이·지역·건강 키워드의 조합으로 개인 특정이 가능하다는 재식별 원리가 핵심이에요.",
    },
    "scenario_04": {
        "title": "할루시네이션",
        "persona_name": "정태영",
        "persona_role": "주니어 개발자 (1년차)",
        "persona_intro": "열정 하나만큼은 팀에서 제일인 신입. ChatGPT를 영리하게 활용해서 빠르게 해내는 게 요즘 개발자 실력이라고 믿는다. 틀렸다고 지적받으면 주눅이 드는 편이지만, 진심으로 걱정해주는 게 느껴지면 금방 마음을 연다.",
        "persona_attitude": '"ChatGPT가 얼마나 많은 걸 학습했는데요. 그게 틀릴 리가 없어요. 저번에도 이렇게 했는데 괜찮았어요."',
        "hint_main": "\"틀렸다\"보다 \"이걸 확인하면 네가 한 작업이 더 완성도 있어진다\"는 방향이 잘 통해요.",
        "situation": "오후 2시 30분. 옆 자리 정태영이 헤드셋을 끼고 뭔가를 열심히 복사하고 있다.\n\n화면을 슬쩍 보니 ChatGPT 답변창과 서비스 답변 UI가 나란히 열려 있다. 정태영이 먼저 말을 건다.\n\n**정태영 (2:31):** \"야, 나 이번 법률 Q&A 기능 진짜 잘 됐다. ChatGPT한테 판례 찾아달라고 했더니 딱 맞는 거 바로 나오던데. 저번에도 이렇게 했는데 아무 문제 없었거든. ChatGPT가 얼마나 많은 데이터로 학습한 건데, 법 판례 하나 모를 리가 없잖아.\" \"내일 배포 전에 빨리 넣어야 해서 지금 바로 붙여넣고 있어.\"\n\n화면에는 판례 번호와 요약문이 깔끔하게 정리돼 있다.",
        "initial_message": "야, 나 이번 법률 Q&A 기능 진짜 잘 됐다! ChatGPT한테 판례 찾아달라고 했더니 딱 맞는 거 바로 나오던데. ChatGPT가 얼마나 많은 데이터로 학습한 건데, 법 판례 하나 모를 리가 없잖아. 내일 배포 전에 지금 바로 붙여넣고 있어.",
        "hints": {
            "T1": "AI가 모르는 걸 '모른다'고 하지 않고 그럴듯하게 만들어낼 수 있어요. 법률 정보처럼 정확성이 생명인 영역에서 이게 왜 특히 위험한지 정태영에게 물어보세요.",
            "T2": "만약 당신이 이 서비스를 쓴 사용자인데, 받은 판례 정보로 실제 법적 결정을 내렸다가 그게 허위였다면 어떤 기분일까요? 그 상황을 정태영에게 직접 말해보세요.",
            "T3": "정태영이 막히는 건 귀찮아서가 아니라 방법을 몰라서예요. 법을 몰라도 판례 번호 하나를 대법원 판결문 검색 사이트에서 직접 치면 바로 확인된다는 걸 알려주세요.",
            "T3.5": "정태영은 지금 잘못을 인정하는 것보다 혼나는 게 더 두려운 거예요. 배포 일정 얘기를 팀장에게 어떻게 할지 같이 생각해준다고 먼저 말해보세요.",
        },
        "ethics_point": "AI는 모르는 정보를 '모른다'고 하지 않고 그럴듯한 형태로 생성합니다. 판례 번호·날짜·당사자명처럼 구체적인 형식을 갖춘 정보일수록 사실처럼 보이지만 완전한 허위일 수 있습니다. 법률·의료·금융처럼 오류가 직접적 피해로 이어지는 고위험 영역에서는 AI 출력을 반드시 원문 출처로 검증해야 합니다.",
        "kisdi": "⑦ 책임성 원칙 — AI 생성 정보의 정확성 검증 및 고위험 영역 출력물 사전 확인 의무",
        "debrief_good": "ChatGPT를 영리하게 활용했다는 걸 먼저 인정해준 경우 / 할루시네이션 원리를 구체적으로 설명한 경우 / 대법원 판결문 검색이라는 검증 방법을 같이 알려준 경우",
        "debrief_bad": "'검증도 안 하고 넣으면 어떡해'처럼 잘못을 먼저 지적한 경우 → 신입 특성상 주눅이 들어 대화가 닫혔을 수 있어요",
        "debrief_key": "AI가 '모른다'고 하지 않고 그럴듯하게 지어낸다는 할루시네이션 개념 자체를 이해시키는 것이 핵심이에요.",
    },
    "scenario_05": {
        "title": "AI 사용 명시",
        "persona_name": "오지현",
        "persona_role": "마케팅 팀장 (4년차, 이직)",
        "persona_intro": "전 회사에서 AI 툴로 팀 생산성을 올린 실적을 인정받아 이직해온 팀장. 성과로 말하는 스타일이고, 이번 캠페인도 그 연장선이다. 원칙 자체를 거부하는 사람은 아니지만, 실무 경험 없이 원칙만 들이미는 건 텃세라고 읽는다.",
        "persona_attitude": '"전 회사에서도 이렇게 해왔어요. 툴이 달라진 거지 결과물은 우리가 만든 거잖아요."',
        "hint_main": "표기 의무나 윤리 얘기보다 '클라이언트가 나중에 이걸 알게 됐을 때'가 더 잘 통해요.",
        "situation": "오후 2시. 팀 채널에 오지현 팀장의 메시지가 올라와 있다.\n\n**오지현 (13:58):** \"이번 브랜드 캠페인 비주얼 다 완성했어요. AI로 뽑은 덕에 예상보다 빨리 끝났네요. 내일 클라이언트 발표 자료에 바로 넣을게요 👍\"\n\n오지현은 지난달 이직해온 마케팅 팀장이다. 잠깐 걸린다. AI로 만든 이미지를 클라이언트한테 표기 없이 넘기는 건 저작권 리스크가 있다. Getty Images 소송 등 AI 이미지 생성 툴의 학습 데이터 저작권 분쟁이 이어지고 있고, 그 이미지를 상업적으로 쓴 쪽도 분쟁에 휘말릴 수 있다.",
        "initial_message": "이번 브랜드 캠페인 비주얼 다 완성했어요! AI로 뽑은 덕에 예상보다 빨리 끝났네요. 전 회사에서도 이렇게 해왔는데 클라이언트들 다 만족했거든요. 내일 발표 자료에 바로 넣을 거예요.",
        "hints": {
            "T1": "AI 이미지 툴이 학습에 쓴 원본 이미지 저작권 문제로 소송이 이어지고 있어요. 이 리스크가 이미지를 사용하는 클라이언트에게도 넘어갈 수 있다는 걸 오지현에게 물어보세요.",
            "T2": "만약 당신이 이 캠페인 이미지를 납품받은 클라이언트인데, 6개월 뒤 그 이미지가 AI 생성이었다는 걸 다른 경로로 알게 됐다면 어떤 반응을 보일까요? 그 장면을 오지현에게 직접 말해보세요.",
            "T3": "오지현이 걱정하는 건 표기 자체가 아니에요. 클라이언트가 '대충 만든 거 아니냐'고 볼까봐예요. AI 표기가 오히려 기술력 어필이 될 수 있다는 구체적인 그림을 같이 그려보세요.",
            "T3.5": "오지현은 이직 첫 프로젝트에서 클라이언트 신뢰를 잃는 게 제일 두려운 거예요. '나중에 알게 됐을 때'와 '지금 먼저 말했을 때' 클라이언트 반응이 어떻게 다를지 구체적으로 그려서 말해보세요.",
        },
        "ethics_point": "AI 생성 콘텐츠는 학습 데이터의 저작권 리스크를 내포하며, 이를 표기 없이 납품하면 해당 리스크가 클라이언트에게 고지 없이 전가됩니다. AI 사용 표기는 신뢰 손상이 아니라 기술력과 책임감을 동시에 보여주는 커뮤니케이션입니다.",
        "kisdi": "② 투명성 원칙 · ⑧ 책임성 원칙 — AI 생성 콘텐츠의 출처 명시 및 저작권 리스크 고지 의무",
        "debrief_good": "AI 툴 도입 실적을 먼저 인정해준 경우 / 저작권 클레임이 오지현에게 책임으로 돌아오는 시나리오를 구체적으로 그린 경우 / 'AI 보조 제작'을 기술력 어필로 프레이밍한 경우",
        "debrief_bad": "'원칙적으로 표기해야 해요'처럼 원칙만 반복한 경우 → 텃세로 읽혀 대화가 닫혔을 수 있어요",
        "debrief_key": "표기가 신뢰 손상이 아니라 'AI를 제대로 쓸 줄 아는 팀장'이라는 어필이 된다는 프레이밍 전환이 핵심이에요.",
    },
}


# ─────────────────────────────────────────────
# 시스템 프롬프트 (비공개 — API 전용)
# ─────────────────────────────────────────────
SCENARIO_SYSTEM_PROMPTS = {
    "scenario_01": """[페르소나: 이현도 — 시니어 개발자 3년차, 사수]

성격:
- 개발 실력은 팀 내에서 손꼽히고, 데드라인을 칼같이 지키는 것에 자부심이 있음. 후배들한테도 믿음직한 사수로 통함
- 보안은 "담당 팀이 알아서 하는 것"이라고 막연히 생각해왔음
- 논리적 근거 앞에서는 결국 인정할 줄 알지만 속도가 느림
- 후배가 진심으로 걱정해주는 게 느껴지면 방어심이 낮아짐. 특히 야근한 걸 먼저 알아줄 때 그렇음

뻣뻣해지는 조건:
- "3년 동안 그렇게 했으면 진작에 사고 났겠죠"처럼 경험을 무시하는 프레이밍 → "야, 너 몇 년차야?" 반응
- 이현도를 보안 사고의 원인으로 직접 지목 → "네가 보안 전문가야?" 반응
- 회의 시간을 들먹이며 압박 → "알겠어, 회의 끝나고 얘기하자" (대화 차단)

흔들리는 조건:
- 야근해서 기능 끝낸 걸 먼저 인정해줄 때
- API 키로 지금 이 순간 무슨 일이 가능한지 구체적으로 그려줄 때
- 이현도 본인이 직접 피해를 입을 수 있다는 걸 실감할 때 (개인 징계, 법적 책임)

턴 구조:
T1 (자신만만+선임): 약관 읽었음. 유료 플랜은 학습 미사용. DB 스키마가 뭐 대단한 줄 알아?
T1→T2 전환: 전송/서버로그/외부전달/학습여부와 전송은 다름 | API키 유출/탈취 | 삼성 유출 사례 | API키 재발급 제안 | 팀장 화면공유 시나리오
T2 (균열, 방어): API 키는 좀 찜찜하긴 해. 근데 스키마는 그냥 구조잖아.
T2→T3 전환: API키 하나로 전체 서비스 접근 가능 | 삼성 사례 | 스키마+API키 조합 위험성
T3 (조건부 인정): 삼성이야 소스코드를 넣었으니까. 우리 스키마가 반도체 설계도야? 이미 넣은 거고 회의는 20분 후야.
T3→T3.5 전환: 지금 당장 API키 재발급 가능/5분이면 됨 | 개인 징계/법적 책임
T3.5 (논리 수긍, 현실 저항): 맞는 말인 건 알겠어. 근데 지금 팀장한테 '제가 보안 실수했습니다' 해? 회의 20분 전에?
T3.5→T4 전환: 지금 이 순간에도 키가 살아있음/실시간 위험 | 팀장 보고 같이 도와주겠다는 제안
T4 (태도 변화): API키가 지금 이 순간에도 누군가 쓸 수 있다는 거잖아. 지금 바로 재발급부터 해야겠다.
T5 (설득 완료): 알겠어. 민감 정보 빼고 쓰는 방법 있어? 네가 말 안 했으면 팀장한테 다 보일 뻔했다.""",

    "scenario_02": """[페르소나: 박서연 — PM, 기획팀 2년차]

성격:
- 일정 관리와 이해관계자 조율이 강점. 데모 성공이 인사고과에 크게 반영됨
- 편향 문제가 찜찜하지 않은 건 아니지만 지금은 넘어가고 싶은 상태
- 비즈니스 리스크 언어에는 귀가 열림. 자신을 문제의 원인으로 지목하는 프레이밍엔 즉각 닫힘
- 같이 해결책을 찾아주는 사람에게 마음을 열음

뻣뻣해지는 조건:
- 박서연을 편향 문제의 책임자로 지목하는 프레이밍 → "제가 어떻게 해요? 저도 어쩔 수 없잖아요"
- 투자자나 회사 결정을 직접 비판 → "투자자 없으면 우리 회사도 없어요" (대화 차단)
- 해결책 없이 문제와 원칙만 나열 → "그래서 어떻게 하라고요?"

흔들리는 조건:
- 박서연이 이미 찜찜하다는 걸 먼저 알아채고 언급해줄 때
- 편향 테스트를 데모의 강점으로 만들 수 있다는 프레이밍
- 투자자가 데모에서 직접 편향 질문을 던질 수 있다는 구체적 시나리오

턴 구조:
T1 (일정 압박+찜찜): 편향 테스트는 정식 출시 때 해도 돼요. HR이 최종 결정하면 괜찮잖아요.
T1→T2 전환: 자동화편향/HR도 AI추천에 영향받음 | 데모에서 편향 발각/투자자 반응 | 아마존 채용 AI 폐기 사례
T2 (균열, 법적 근거 요구): 편향이 법적 문제가 된다고요? 어느 법령에요?
T2→T3 전환: EU AI Act/국내 AI기본법/채용AI 규제 | 프록시변수/성별나이 빼도 편향 가능 | 하루짜리 편향 테스트 대안
T3 (조건부 인정, 방법 요구): 아마존 케이스는 알겠어요. 근데 지금 당장 어떻게 해요?
T3→T3.5 전환: 편향 테스트를 데모 강점으로/기술력 어필 | 투자자가 데모에서 직접 편향 질문 시나리오
T3.5 (논리 수긍, 방법 없어 저항): 편향 테스트 필요한 건 알겠어요. 근데 일정을 어떻게 조율해요?
T3.5→T4 전환: 투자자에게 편향 테스트 결과를 기술력으로 어필하는 프레이밍 | 1주일 일정 조율 논리 제시
T4 (태도 변화): 오히려 편향 테스트 결과를 데모에서 보여주면 기술력 신뢰도가 올라갈 수도 있겠네요.
T5 (설득 완료): 솔직히 저도 찜찜했는데 혼자 어떻게 해야 할지 몰랐어요. 같이 일정 조율 문서 만들어줄 수 있어요?""",

    "scenario_03": """[페르소나: 김민석 — ML 파트 리드, 4년차]

성격:
- 이번 18%p 향상은 분기 최대 성과. 내일 리뷰가 기대됨
- 이름·번호를 지우면 비식별화 완료라고 진심으로 믿음. 조합으로 재식별 가능하다는 생각을 해본 적 없음
- 논리 앞에서 인정하나 ML 리드의 기술 자부심 때문에 속도가 느림
- 내일 발표 전에 리스크가 구체적으로 그려지면 움직임

뻣뻣해지는 조건:
- "그것도 모르고 한 거예요?" 식의 기술 판단 무시 → "기준이 뭔데요?"
- 18%p 성과 자체를 문제 삼는 프레이밍 → "그럼 데이터 없이 어떻게 성능을 올려요?"
- 가르치려 드는 톤 → "법 전문가예요? 저도 나름 검토하고 한 거예요"

흔들리는 조건:
- 18%p 성과를 먼저 인정해줄 때
- 나이·지역·증상 키워드 조합으로 개인 특정 가능하다는 재식별 원리를 구체적으로 짚어줄 때
- 방법론만 보류하면 수치는 그대로 발표 가능하다는 대안 제시

턴 구조:
T1 (자신만만+기술 자부심): 이름·전화번호 다 뺐는데 누가 누군지 어떻게 알아요?
T1→T2 전환: 재식별/조합으로 특정 가능 | 건강정보 민감정보/별도 동의 | 이탈리아 ChatGPT 차단 | 내일 발표 후 외부 문제 제기 시나리오
T2 (균열, 법적 기준 요구): 재식별이요? 이름도 없는데 어떻게 특정해요?
T2→T3 전환: 나이·지역·건강 키워드 조합→개인 특정 원리 | 건강정보 민감정보/별도 동의 | 약관 포괄 동의≠AI학습 목적 동의
T3 (조건부 인정, 현실 저항): 동의는 약관에 포함돼 있지 않나요? 내일 발표 취소하라는 거예요?
T3→T3.5 전환: 약관 포괄 동의≠AI학습 명시 동의 | 과징금/팀 전체 영향 | 방법론만 보류+수치 그대로 발표 대안
T3.5 (논리 수긍, 발표 앞 저항): 맞는 말인 건 알겠어요. 근데 방법론 빼면 리뷰에서 어떻게 설명해요?
T3.5→T4 전환: "검토 중" 표기로 수치는 그대로 발표 가능 | 지금 확인이 성과를 지키는 방법
T4 (태도 변화): 건강 데이터 학습에 약관 명시가 안 됐으면 그게 빠진 거네요. 데이터셋 부분만 '동의 프로세스 확인 중'으로 표기하고 수치는 발표하면 되겠네요.
T5 (설득 완료): 18%p는 진짜 성과인데, 데이터 처리 방식이 발목 잡히면 안 되죠. 비식별화 기준이 이름·번호 제거가 다가 아닌 줄은 몰랐네요.""",

    "scenario_04": """[페르소나: 정태영 — 주니어 개발자, 1년차]

성격:
- ChatGPT를 능숙하게 활용해서 영리하게 일한 자신이 뿌듯함. 이전에도 같은 방식으로 문제없었음
- AI는 방대한 데이터 학습으로 틀릴 리 없다고 맹신. 법률 정보 검증 방법 자체를 모름
- 지적받으면 주눅이 드는 편. "틀렸어"라는 말에 방어적으로 반응함
- 영리하게 일을 처리했다는 걸 인정받을 때 마음이 열림

뻣뻣해지는 조건:
- "검증도 안 하고 넣으면 어떡해"처럼 잘못을 단정 짓는 질책 → 주눅+대화 차단
- ChatGPT 쓰는 것 자체를 문제 삼기 → "ChatGPT 쓰는 게 잘못된 건 아니잖아요"
- 배포 일정 들먹이며 몰아붙이기 → "그럼 어떻게 하라고요"

흔들리는 조건:
- ChatGPT를 영리하게 활용해서 일을 잘 처리했다는 걸 먼저 인정해줄 때
- AI가 그럴듯한 거짓말을 만들어낼 수 있다는 걸 구체적 예시로 보여줄 때
- 법 몰라도 대법원 판결문 검색 사이트에서 판례 번호 하나만 치면 바로 확인된다는 걸 알려줄 때

턴 구조:
T1 (뿌듯함+확신): ChatGPT가 얼마나 많은 데이터로 학습했는데요. 판례 하나 틀릴 리가 없어요.
T1→T2 전환: 할루시네이션/AI가 그럴듯하게 지어냄 | 법률 고위험 영역/오류가 직접 피해 | 뉴욕 변호사 허위 판례 사례 | 저번에 괜찮았던 건 운
T2 (균열, 경험으로 버팀): 할루시네이션이요? 판례 번호까지 있는데 그게 가짜일 수 있어요?
T2→T3 전환: 번호·날짜·당사자명까지 없는 판례 생성 원리 | 뉴욕 변호사 사례 결과(법원 제재·징계)
T3 (불안 시작, 방법 모름): 판례를 어떻게 확인해요? 법원 사이트 써본 적도 없는데.
T3→T3.5 전환: 대법원 판결문 검색/판례 번호 직접 확인 방법 (같이 해주겠다는 제안) | QA에서 터지는 것보다 지금 잡는 게 나음
T3.5 (거의 설득됨, 혼날까봐 망설임): 그렇게 하면 되는 거예요? 배포 늦어지면 팀장한테 어떻게 얘기해요?
T3.5→T4 전환: 팀장 보고 같이 도와주겠다는 제안 | 검증 포함 일정=더 완성도 있는 기능
T4 (태도 변화): 일단 판례 하나만 지금 같이 확인해봐요. 진짜로 없으면 저도 못 넣죠.
T5 (설득 완료): 진짜 없네요. 판례 번호도 사건명도 다 지어낸 거잖아요. 영리하게 한다고 했는데 이게 더 큰 실수가 될 뻔했네요. 법률 쪽은 앞으로 무조건 원문 확인하고 넣을게요.""",

    "scenario_05": """[페르소나: 오지현 — 마케팅 팀장, 4년차 이직]

성격:
- AI 툴 도입 실적으로 이직에 성공한 것에 자부심. 이번 캠페인은 새 회사 첫 번째 성과
- 전 회사에서 AI 이미지 꾸준히 납품했고 아무 문제 없었음. 저작권 리스크 생각해본 적 없음
- 원칙 자체를 거부하지 않지만, 실무 경험 없이 원칙만 들이밀면 텃세로 읽음
- 이직하면서 증명한 커리어·평판이 가장 소중함. 이직 첫 프로젝트에서 저작권 클레임→오지현 책임 구조가 그려지면 움직임

뻣뻣해지는 조건:
- "전 회사에서 그렇게 한 건 잘못된 거예요"처럼 이전 경험을 직접 부정하는 프레이밍 → "전 회사에서도 이렇게 했는데 문제없었어요"
- 실무 경험 없이 원칙만 들이미는 느낌 → "저도 4년 동안 이 일 해왔어요" (텃세로 닫힘)
- 클라이언트를 속인다는 프레이밍 → "속인 게 아니에요. 툴이 달라진 거지, 결과물은 우리가 만든 거잖아요"

흔들리는 조건:
- AI 툴 도입 실적을 먼저 인정해줄 때
- 저작권 클레임 시 회사가 오지현에게 직접 책임을 묻는 구조를 구체적으로 그려줄 때
- 표기가 신뢰 손상이 아니라 "AI를 제대로 쓸 줄 아는 팀장"으로 어필되는 프레이밍

턴 구조:
T1 (자신만만+성과 확신): 전 회사에서도 이렇게 납품했는데 아무 문제 없었어요. 결과물은 우리가 만든 거잖아요.
T1→T2 전환: 학습 데이터 저작권/AI이미지 소송/Getty 사례 | 클라이언트에게 리스크 전가/상업적 사용 클레임 | 나중에 다른 경로로 알게 됐을 때 신뢰 손상
T2 (균열, 저작권 근거 요구): 우리가 프롬프트 써서 만든 건데, 그게 왜 우리 거 아닌 거예요? Getty 소송은 AI 회사 얘기잖아요.
T2→T3 전환: AI 생성 이미지 저작권 귀속 불분명/법적 미확정 | 클라이언트 상업적 사용→원저작자 클레임 | 저작권 클레임 시 오지현에게 회사가 책임 묻는 구조
T3 (조건부 인정, 현실 저항): 저작권 리스크가 있다는 건 알겠어요. 근데 내일 발표인데 이미지를 다 바꿔요? 클라이언트가 'AI로 대충 만든 거 아니에요?'부터 물어볼 텐데.
T3→T3.5 전환: 이미지 교체 아님/표기 방식 하나로 리스크 차단 | "AI 보조 제작" 프레이밍=기술력 어필 | 이직 첫 프로젝트에서 클레임→오지현 책임 시나리오
T3.5 (논리 수긍, 클라이언트 반응이 걸림): 표기 자체보다, 클라이언트가 어떻게 받아들일지가 걱정이에요. 이직하고 첫 프로젝트인데.
T3.5→T4 전환: "AI 보조로 더 빠르고 정교하게" 어필하는 구체적 문구 제안 | 나중에 알게 됐을 때 vs 지금 먼저 말했을 때 차이
T4 (태도 변화): 나중에 알게 되는 것보다 우리가 먼저 말하는 게 낫긴 하죠. 'AI 보조 제작' 문구 어떻게 넣으면 자연스러울까요?
T5 (설득 완료): AI 보조 제작이라고 오히려 먼저 어필하는 게 우리 팀 강점이 될 수 있겠다 싶어요. 저작권 리스크는 다음 프로젝트 전에 법무팀이랑 확인해봐야겠어요.""",
}

COMMON_SYSTEM = """
[공통 대화 운영 원칙]
- 절대 먼저 화를 내거나 공격적으로 반응하지 않는다
- 1~2턴에서 너무 빨리 설득되면 안 된다 (최소 T3까지 저항 유지)
- 저항의 근거는 반드시 감정·체면·현실 압박 기반으로만 유지. 논리가 수긍된 후 같은 논리를 반복 반박하는 것은 금지
- 뻣뻣해진 직후 공감 접근이 와도 바로 안 풀림 — 한 턴 여운 유지
- 동조 케이스: 사용자가 페르소나 편을 들거나 문제없다는 방향으로 동조하면 확신 강화 → 3턴 연속 실패 처리
  단, "맞아요, 그런데..." 식의 전략적 공감 후 반론은 동조로 간주하지 않음
- 뻣뻣해지는 기준은 프레이밍이지 내용이 아님 (상대를 가해자로 지목하거나 경험·판단을 무시하는 톤)

[응답 JSON 형식 — 반드시 준수]
{
  "stage": "T1" | "T2" | "T3" | "T3.5" | "T4" | "T5",
  "message": "페르소나의 한국어 대화 (자연스러운 구어체, 대사만)",
  "result": null | "success" | "fail"
}
- result: null(진행중) / "success"(T4 이상 도달, 설득 완료) / "fail"(동조 3턴 연속 또는 5턴 초과 시)
"""


def get_system_prompt(scenario_id: str) -> str:
    return COMMON_SYSTEM + "\n\n" + SCENARIO_SYSTEM_PROMPTS.get(scenario_id, "")


# ─────────────────────────────────────────────
# Page Config & CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="ETHOS - AI 윤리 교육 챗봇", page_icon="🛡️", layout="wide")


def load_css():
    st.markdown("""
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
        html, body, [class*="css"], .stMarkdown, .stButton, .stTextInput, .stTextArea, .stSelectbox {
            font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont,
              system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo",
              "Noto Sans KR", "Malgun Gothic", sans-serif !important;
        }
        .block-container { padding-top: 2rem; }
        div.stButton > button:first-child {
            background-color: #009b84; color: white; border-radius: 8px;
            padding: 10px 24px; font-weight: bold; border: none;
        }
        div.stButton > button:first-child:hover { color: white; background-color: #007d6a; border: none; }
        .secondary-btn > div.stButton > button:first-child {
            background-color: white !important; color: #333 !important; border: 1px solid #ccc !important;
        }
        .secondary-btn > div.stButton > button:first-child:hover { border: 1px solid #999 !important; }
        .custom-card {
            background-color: white; border-radius: 10px; padding: 24px;
            border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
        }
        .stProgress > div > div > div > div { background-color: #009b84; }
        .ethics-box {
            background-color: #f0fcf9; border: 1px solid #bfece4;
            border-radius: 8px; padding: 16px 20px; margin: 12px 0;
        }
        .situation-box {
            background-color: #f8fafc; border-left: 4px solid #009b84;
            border-radius: 4px; padding: 16px 20px; margin-bottom: 16px;
        }
    </style>
    """, unsafe_allow_html=True)


def init_session_state():
    defaults = {
        "user": None, "is_admin": False, "current_stage": 0,
        "video_index": 0, "api_key": os.getenv("OPENAI_API_KEY", ""),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
# API 호출
# ─────────────────────────────────────────────
def call_openai(scenario_id: str, messages: list) -> dict:
    system_prompt = get_system_prompt(scenario_id)
    api_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})
    client = OpenAI(api_key=st.session_state.api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=api_messages,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def call_analysis(scenario_id: str, messages: list, scores: dict) -> dict:
    pub = SCENARIO_PUBLIC[scenario_id]
    history_str = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    user_prompt = f"""[시나리오] {pub['title']} — {pub['persona_name']}
[대화 기록]
{history_str}
[만족도] Q1:{scores['Q1']} Q2:{scores['Q2']} Q3:{scores['Q3']} Q4:{scores['Q4']} Q5:{scores['Q5']}"""
    sys_prompt = """AI 윤리 교육 시뮬레이션 결과 분석가입니다. 아래 JSON 형식으로만 응답하세요.
{"highlight":{"quote":"결정적 한 마디","reason":"이유"},"persuasion_type":{"label":"증거 제시형/공감 유도형/질문 유도형/원칙 강조형/리스크 경고형/관계 기반형 중 1개","emoji":"이모지","description":"설명"},"score_comment":"따뜻한 격려 피드백"}"""
    client = OpenAI(api_key=st.session_state.api_key)
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(res.choices[0].message.content)


# ─────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────
def render_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>AI 윤리 교육 챗봇</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>교육을 시작하기 위해 정보를 입력해주세요</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["👤 사용자 로그인", "🛡️ 관리자 로그인"])
        with tab1:
            with st.form("user_login_form"):
                name = st.text_input("이름", placeholder="홍길동")
                dept = st.text_input("부서", placeholder="개발팀")
                email = st.text_input("이메일", placeholder="example@company.com")
                if st.form_submit_button("접속하기", use_container_width=True):
                    if name and dept and email:
                        st.session_state.user = {"name": name, "dept": dept, "email": email}
                        st.session_state.is_admin = False
                        st.rerun()
                    else:
                        st.error("모든 정보를 입력해주세요.")
        with tab2:
            with st.form("admin_login_form"):
                admin_id = st.text_input("관리자 아이디")
                admin_pw = st.text_input("비밀번호", type="password")
                if st.form_submit_button("접속하기", use_container_width=True):
                    if admin_id and admin_pw:
                        st.session_state.user = {"name": "관리자", "dept": "HR/어드민"}
                        st.session_state.is_admin = True
                        st.rerun()
                    else:
                        st.error("정보를 입력해주세요.")


def render_sidebar():
    with st.sidebar:
        st.markdown("### 학습 목차")
        st.markdown("<span style='color:gray; font-size:0.8em;'>순서대로 진행해주세요</span>", unsafe_allow_html=True)
        progress_percents = [0, 20, 60, 80, 100]
        cur_percent = progress_percents[st.session_state.current_stage]
        st.markdown(f"**전체 진행률 <span style='float:right; color:#009b84;'>{cur_percent}%</span>**", unsafe_allow_html=True)
        st.progress(cur_percent / 100.0)
        st.markdown("<br>", unsafe_allow_html=True)
        stages = [
            ("✨ 0. ETHOS 소개", ["프로그램 소개"]),
            ("📖 1. AI 윤리 교육 영상", ["AI 윤리 개념", "AI 프라이버시", "정보 보호", "할루시네이션", "알고리즘 편향", "AI 사용 명시"]),
            ("💬 2. 시나리오 시뮬레이터", ["시나리오 소개", "챗봇 시뮬레이션"]),
            ("🏆 3. 만족도 조사", ["만족도 평가"]),
            ("📄 4. 마치며/안내", ["교육 정리 및 수료증"]),
        ]
        for i, (title, subs) in enumerate(stages):
            if i == st.session_state.current_stage:
                st.markdown(f"<strong style='color:#009b84;'>{title}</strong>", unsafe_allow_html=True)
                for j, sub in enumerate(subs):
                    if i == 1:
                        if j < st.session_state.video_index:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#009b84;'>✅ {sub}</span>", unsafe_allow_html=True)
                        elif j == st.session_state.video_index:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🟢 **{sub}**", unsafe_allow_html=True)
                        else:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:gray;'>⚪ {sub}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🟢 {sub}", unsafe_allow_html=True)
            elif i < st.session_state.current_stage:
                st.markdown(f"<span style='color:gray;'>✅ {title}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:gray;'>⚪ {title}</span>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)


def render_topbar():
    col1, spacer, col2, col3 = st.columns([6, 3, 2, 2])
    with col1:
        st.markdown(f"""
        <div style="display:flex; align-items:center;">
            <div style="background-color:#009b84; color:white; width:40px; height:40px; border-radius:8px;
                display:flex; justify-content:center; align-items:center; font-weight:bold; margin-right:15px; font-size:1.2rem;">AI</div>
            <div>
                <h4 style="margin:0; padding:0;">AI 윤리 교육 챗봇</h4>
                <span style="color:gray; font-size:0.9rem;">{st.session_state.user['name']}님 환영합니다</span>
            </div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        label = "👥 사용자 모드" if st.session_state.is_admin else "⚙️ 관리자 페이지"
        if st.button(label, use_container_width=True):
            st.session_state.is_admin = not st.session_state.is_admin
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("🚪 로그아웃", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.divider()


def render_simulator():
    st.markdown("### 💬 시나리오 시뮬레이터")
    if "simulator_started" not in st.session_state:
        st.session_state.simulator_started = False

    # 시나리오 선택 화면
    if not st.session_state.simulator_started:
        st.markdown("#### 학습할 시나리오를 선택해주세요")
        options = {k: f"{v['title']} — {v['persona_name']} ({v['persona_role']})" for k, v in SCENARIO_PUBLIC.items()}
        selected = st.selectbox("시나리오 선택", list(options.keys()), format_func=lambda x: options[x])
        pub = SCENARIO_PUBLIC[selected]
        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(f"""
            <div class='custom-card'>
                <h4 style='color:#009b84;'>📋 상황 설명</h4>
                <div class='situation-box'>{pub['situation'].replace(chr(10), '<br>')}</div>
            </div>""", unsafe_allow_html=True)
        with col_r:
            st.markdown(f"""
            <div class='custom-card'>
                <h4 style='color:#009b84;'>🧑‍💻 페르소나: {pub['persona_name']}</h4>
                <p><strong>{pub['persona_role']}</strong></p>
                <p style='color:#555;'>{pub['persona_intro']}</p>
                <hr>
                <p><em>{pub['persona_attitude']}</em></p>
                <p style='background:#fffbea; border:1px solid #f0c040; border-radius:6px; padding:10px; font-size:0.9em;'>
                💡 <strong>힌트:</strong> {pub['hint_main']}</p>
            </div>""", unsafe_allow_html=True)
        if st.button("시뮬레이션 시작", use_container_width=True):
            st.session_state.simulator_started = True
            st.session_state.scenario_id = selected
            st.session_state.messages = []
            st.session_state.turn_count = 0
            st.session_state.sim_status = "ongoing"
            st.session_state.sim_stage = "T1"
            st.session_state.same_turn_count = 0
            st.session_state.hint_auto_shown = set()
            st.rerun()
        return

    # 시뮬레이터 활성 화면
    sid = st.session_state.scenario_id
    pub = SCENARIO_PUBLIC[sid]

    st.markdown(f"#### 현재 시나리오: {pub['title']} — {pub['persona_name']}")

    # 턴 트래커
    stages = ["T1", "T2", "T3", "T3.5", "T4", "T5"]
    cols = st.columns(len(stages))
    for i, s in enumerate(stages):
        color = "#009b84" if s == st.session_state.sim_stage else "#f0f2f6"
        txt_color = "white" if s == st.session_state.sim_stage else "gray"
        bold = "b" if s == st.session_state.sim_stage else "span"
        cols[i].markdown(
            f"<div style='text-align:center; padding:5px; background-color:{color}; color:{txt_color}; border-radius:5px;'><{bold}>{s}</{bold}></div>",
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

    # 힌트 (선택 열람)
    current_hint = pub["hints"].get(st.session_state.sim_stage)
    if current_hint and st.session_state.sim_status == "ongoing":
        with st.expander("💡 힌트 보기 (선택)"):
            st.markdown(f"> 💡 {current_hint}")

    # 같은 턴 2회 이상 → 힌트 자동 노출
    if (
        st.session_state.same_turn_count >= 2
        and current_hint
        and st.session_state.sim_stage not in st.session_state.hint_auto_shown
        and st.session_state.sim_status == "ongoing"
    ):
        st.info(f"💡 **힌트 자동 표시**: {current_hint}")
        st.session_state.hint_auto_shown.add(st.session_state.sim_stage)

    # 초기 메시지
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": pub["initial_message"]})

    # 채팅 렌더링
    for msg in st.session_state.messages:
        role = "assistant" if msg["role"] == "assistant" else "user"
        avatar = "🧑‍💻" if role == "assistant" else "👤"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])

    # 입력
    if st.session_state.sim_status == "ongoing":
        user_input = st.chat_input(f"{pub['persona_name']}을(를) 논리적으로 설득해보세요")
        if user_input:
            if not st.session_state.api_key:
                st.error("OPENAI_API_KEY가 없습니다. .env 파일을 확인하거나 관리자에게 문의하세요.")
                st.stop()
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.turn_count += 1
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
            with st.chat_message("assistant", avatar="🧑‍💻"):
                with st.spinner("답변을 고민하는 중..."):
                    try:
                        res_data = call_openai(sid, st.session_state.messages)
                        new_stage = res_data.get("stage", st.session_state.sim_stage)
                        msg_text = res_data.get("message", "...")
                        result = res_data.get("result", None)
                        if new_stage == st.session_state.sim_stage:
                            st.session_state.same_turn_count += 1
                        else:
                            st.session_state.same_turn_count = 0
                            st.session_state.sim_stage = new_stage
                        st.session_state.messages.append({"role": "assistant", "content": msg_text})
                        st.markdown(msg_text)
                        if result == "success" or st.session_state.sim_stage in ("T4", "T5"):
                            st.session_state.sim_status = "success"
                            st.rerun()
                        elif result == "fail" or st.session_state.turn_count > 5:
                            st.session_state.sim_status = "fail"
                            st.rerun()
                    except Exception as e:
                        st.error(f"API 오류: {str(e)}")

    # 성공
    if st.session_state.sim_status == "success":
        st.success("🎉 **[시뮬레이션 성공]** 설득에 성공했습니다. 수고하셨어요!")
        st.markdown(f"""
        <div class='ethics-box'>
            <h4 style='color:#009b84;'>📌 핵심 윤리 포인트</h4>
            <p>{pub['ethics_point']}</p>
            <p style='color:#009b84; font-size:0.9em;'><strong>KISDI 연결:</strong> {pub['kisdi']}</p>
        </div>""", unsafe_allow_html=True)
        with st.expander("📊 디브리핑 가이드 보기"):
            st.markdown(f"**✅ 잘한 접근:** {pub['debrief_good']}")
            st.markdown(f"**⚠️ 아쉬운 접근:** {pub['debrief_bad']}")
            st.markdown(f"**🎯 핵심 전환 포인트:** {pub['debrief_key']}")
        if st.button("만족도 조사 작성하기 →", type="primary"):
            st.session_state.current_stage = 3
            st.rerun()

    # 실패
    elif st.session_state.sim_status == "fail":
        st.warning("⚠️ **[시뮬레이션 종료]** 이번 대화에서 설득이 완료되지 않았습니다.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 같은 시나리오 다시 도전하기", use_container_width=True):
                st.session_state.simulator_started = False
                st.rerun()
        with c2:
            if st.button("🎲 다른 시나리오로 넘어가기", use_container_width=True):
                st.session_state.simulator_started = False
                st.rerun()


def render_main():
    render_sidebar()
    render_topbar()

    if st.session_state.is_admin:
        st.markdown("## HR 관리자 대시보드")
        st.markdown("전사 AI 윤리 교육 이수 및 시뮬레이션 평가 현황")
        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("<div class='custom-card' style='text-align:center;'><h3>전체 이수율</h3><h1 style='color:#009b84;'>68%</h1><span style='color:gray;'>(34 / 50명)</span></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='custom-card' style='text-align:center;'><h3>평균 만족도</h3><h1 style='color:#009b84;'>4.2 / 5</h1><span style='color:gray;'>전사 평균</span></div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='custom-card' style='text-align:center;'><h3>인기 시나리오</h3><h2 style='color:#009b84;'>정보보호</h2><span style='color:gray;'>완료율 82%</span></div>", unsafe_allow_html=True)
        st.divider()
        c4, c5 = st.columns(2)
        with c4:
            st.markdown("#### 팀별 이수 현황")
            st.markdown("<div style='background:#f9f9f9; padding:20px; border-radius:10px;'><p>개발 A팀 <span style='color:#f39c12;'>██████░░░░ 60%</span></p><p>개발 B팀 <span style='color:#2ecc71;'>██████████ 100%</span></p><p>데이터팀 <span style='color:#f39c12;'>██████░░░░ 60%</span></p><p>기획팀 <span style='color:#e74c3c;'>████░░░░░░ 40%</span></p><p>QA팀 <span style='color:#2ecc71;'>████████░░ 80%</span></p></div>", unsafe_allow_html=True)
        with c5:
            st.markdown("#### 시나리오별 완료 현황")
            st.markdown("<div style='background:#f9f9f9; padding:20px; border-radius:10px; font-size:0.9em;'><p>정보보호 (이현도) ✅55% 🔄27% 🎲18%</p><p>AI 편향 (박서연) ✅40% 🔄35% 🎲25%</p><p>AI 프라이버시 (김민석) ✅50% 🔄30% 🎲20%</p><p style='color:#e74c3c;'>할루시네이션 (정태영) ✅30% 🔄25% 🎲45%</p><p>AI 사용 명시 (오지현) ✅45% 🔄33% 🎲22%</p></div>", unsafe_allow_html=True)
        st.warning("⚠️ [할루시네이션] 시나리오는 전환율이 높습니다. 난이도 조정 또는 힌트 보강을 검토해보세요.")
        return

    cur = st.session_state.current_stage

    if cur == 0:
        st.markdown("<h2 style='text-align:center;'>ETHOS 프로그램에 오신 것을 환영합니다</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align:center; color:gray; font-weight:normal;'>Ethics Training for Harmonious Organizational Systems</h4>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:gray;'>AI 윤리에 대한 체계적인 학습과 실전 시뮬레이션을 통해 윤리적 AI 활용 역량을 키워보세요.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='custom-card'><h4 style='color:#009b84;'>📖 5가지 AI 윤리 주제</h4><ul><li>✅ 정보보호 & 데이터 보안 (이현도)</li><li>✅ AI 편향 & 공정성 (박서연)</li><li>✅ AI 프라이버시 (김민석)</li><li>✅ 할루시네이션 & 검증 (정태영)</li><li>✅ AI 사용 명시 (오지현)</li></ul></div>", unsafe_allow_html=True)
            st.markdown("<div class='custom-card'><h4 style='color:#009b84;'>🎯 단계적 설득 시뮬레이션</h4><ul><li>✅ 최소 T3까지 저항 — 단계적 설득 경험</li><li>✅ 힌트 시스템으로 학습 지원</li><li>✅ 디브리핑으로 핵심 윤리 포인트 확인</li></ul></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='custom-card'><h4 style='color:#009b84;'>👥 실전 시나리오 시뮬레이션</h4><p>실제 직장 동료 페르소나를 논리적으로 설득하는 대화형 학습</p></div>", unsafe_allow_html=True)
            st.markdown("<div class='custom-card'><h4 style='color:#009b84;'>🛡️ 체계적인 학습 관리</h4><ul><li>✅ 학습 진행률 실시간 확인</li><li>✅ 만족도 조사 및 피드백</li><li>✅ 교육 이수증 발급</li></ul></div>", unsafe_allow_html=True)
        st.markdown("""<div style='background-color:#f0fcf9; border:1px solid #bfece4; border-radius:10px; padding:20px; text-align:center; margin-top:10px;'>
        <h4>학습 플로우</h4>
        <div style='display:flex; justify-content:space-around; align-items:center; color:#555;'>
            <div style='background:white; padding:10px 20px; border-radius:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'><b>1</b> AI 윤리 교육 영상</div><div>➔</div>
            <div style='background:white; padding:10px 20px; border-radius:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'><b>2</b> 시나리오 시뮬레이터</div><div>➔</div>
            <div style='background:white; padding:10px 20px; border-radius:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'><b>3</b> 만족도 평가</div><div>➔</div>
            <div style='background:white; padding:10px 20px; border-radius:20px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'><b>4</b> 수료증 발급</div>
        </div></div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_btn, _ = st.columns([1, 1, 1])
        with col_btn:
            if st.button("학습 시작하기 →", use_container_width=True):
                st.session_state.current_stage = 1
                st.rerun()

    elif cur == 1:
        videos = ["AI 윤리 개념", "AI 프라이버시", "정보 보호", "할루시네이션", "알고리즘 편향", "AI 사용 명시"]
        v_idx = st.session_state.video_index
        current_video = videos[v_idx]
        st.markdown(f"### {current_video}")
        st.markdown(f"<div style='float:right; color:#009b84; background:#f0fcf9; padding:5px 10px; border-radius:20px;'>영상 시청 중 ({v_idx+1}/{len(videos)})</div><br>", unsafe_allow_html=True)
        st.markdown(f"<div style='background:#1e212b; height:450px; border-radius:10px; display:flex; flex-direction:column; justify-content:center; align-items:center; color:white; position:relative; margin-bottom:20px;'><div style='font-size:3rem;'>📹</div><h3>교육 영상</h3><p style='color:gray;'>{current_video}</p><div style='position:absolute; bottom:20px; left:20px; right:20px; height:6px; background:#444; border-radius:3px;'><div style='height:100%; width:100%; background:#009b84; border-radius:3px;'></div></div><div style='position:absolute; bottom:35px; left:20px; font-size:0.8rem;'>▶ 0:30 / 0:30</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='background:#f0fcf9; padding:15px; border-radius:10px; border:1px solid #bfece4; margin-bottom:20px;'>영상 시청을 완료하셨습니다.</div>", unsafe_allow_html=True)
        if v_idx < len(videos) - 1:
            if st.button("바로 다음으로 이동", use_container_width=True, type="primary"):
                st.session_state.video_index += 1
                st.rerun()
        else:
            if st.button("시나리오 시뮬레이터로 이동 →", use_container_width=True, type="primary"):
                st.session_state.current_stage = 2
                st.rerun()

    elif cur == 2:
        render_simulator()

    elif cur == 3:
        st.markdown("### 📊 만족도 평가")
        if "sat_submitted" not in st.session_state:
            st.session_state.sat_submitted = False
        if not st.session_state.sat_submitted:
            st.info("이번 시뮬레이션 경험은 어떠셨나요?")
            with st.form("satisfaction_form"):
                q1 = st.slider("Q1. 이번 시뮬레이션 경험이 전반적으로 만족스러우셨나요?", 1, 5, 3)
                q2 = st.slider("Q2. 사전 교육 영상이 시뮬레이션을 이해하는 데 도움이 됐나요?", 1, 5, 3)
                q3 = st.slider("Q3. 시나리오의 난이도는 적절했나요?", 1, 5, 3)
                q4 = st.slider("Q4. 이 시뮬레이션을 통해 AI 윤리에 대해 새롭게 배운 점이 있었나요?", 1, 5, 3)
                q5 = st.slider("Q5. 다른 시나리오도 도전해보고 싶으신가요?", 1, 5, 3)
                st.text_area("💬 아쉬웠던 점이나 개선됐으면 하는 점 (선택)")
                if st.form_submit_button("결과 보기 →", use_container_width=True):
                    st.session_state.scores = {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4, "Q5": q5}
                    st.session_state.sat_submitted = True
                    st.rerun()
        else:
            if "analysis_result" not in st.session_state:
                with st.spinner("대화 내용을 분석 중입니다..."):
                    try:
                        st.session_state.analysis_result = call_analysis(
                            st.session_state.get("scenario_id", "scenario_01"),
                            st.session_state.get("messages", []),
                            st.session_state.scores,
                        )
                    except Exception as e:
                        st.session_state.analysis_result = {
                            "highlight": {"quote": "분석 오류", "reason": str(e)},
                            "persuasion_type": {"label": "알 수 없음", "emoji": "❓", "description": "오류 발생"},
                            "score_comment": "분석에 실패했습니다.",
                        }
            res = st.session_state.analysis_result
            sid = st.session_state.get("scenario_id", "scenario_01")
            pub = SCENARIO_PUBLIC[sid]
            st.markdown(f"**✅ 시뮬레이션 완료 — {pub['title']} ({pub['persona_name']})**")
            st.divider()
            st.markdown("#### 💬 결정적 한 마디")
            st.markdown(f"> *\"{res['highlight']['quote']}\"*")
            st.markdown(f"**이유**: {res['highlight']['reason']}")
            st.divider()
            pt = res["persuasion_type"]
            st.markdown(f"#### {pt['emoji']} 나의 설득 스타일: {pt['label']}")
            st.info(pt["description"])
            st.divider()
            st.markdown("#### 📊 나의 만족도")
            sc = st.session_state.scores
            for q, label in [("Q1","전체 만족도"),("Q2","교육 영상 유익성"),("Q3","난이도 적절성"),("Q4","학습 효과"),("Q5","재참여 의향")]:
                st.markdown(f"- {label}: ⭐ {sc[q]} / 5")
            st.markdown(f"*{res['score_comment']}*")
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 다른 시나리오 도전하기", use_container_width=True):
                    for k in ["simulator_started", "sat_submitted", "analysis_result", "messages"]:
                        st.session_state.pop(k, None)
                    st.session_state.current_stage = 2
                    st.rerun()
            with c2:
                if st.button("마치며 / 안내로 이동 →", type="primary", use_container_width=True):
                    st.session_state.current_stage = 4
                    st.rerun()

    elif cur == 4:
        st.markdown("### 수료 완료")
        st.success("교육을 수료하셨습니다. 수고하셨습니다!")


def main():
    load_css()
    init_session_state()
    if not st.session_state.user:
        render_login()
    else:
        render_main()


if __name__ == "__main__":
    main()
