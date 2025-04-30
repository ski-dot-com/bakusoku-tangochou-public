from time import sleep, monotonic_ns
from re import compile, Match
from time import monotonic_ns

from ..core import Difficulty, CustomDifficulty, DIF2NUMS, Level, Question, DIFFICULTY_NAMES, TIME_CONST_FACTOR, TIME_PROPO_FACTOR, LEVEL_NAMES
from ..core.util import ask_yes_no
from .menu_graphic import configure
from .config import config
from .session import Session

RE_ANSWER=compile(r"{(.*?)}")

def show_mondai(data:str):
    if data:
        data+="\n"
    print(f"""
                                                                                                                         
                                                                                                                         
                                                                                                                         
                ██████████████████    ██████████████████        ██████████████████  ██████████████████████  
                ████          ████    ████          ████        ████          ████          ████            
                ████          ████    ████          ████        ████          ████          ████            
                ████          ████    ████          ████        ██████████████████          ██              
                ██████████████████    ██████████████████        ████          ████    ██████████████████    
                ████          ████    ████          ████        ████          ████    ██            ████    
                ████          ████    ████          ████        ██████████████████    ██            ████    
                ██████████████████    ██████████████████                              ██████████████████    
                ████                                ████                              ██            ████    
                ████                                ████      ██████████████████████  ██            ████    
                ████      ████████████████████      ████                ████          ██████████████████    
                ████      ████            ████      ████                ████          ██            ████    
                ████      ████            ████      ████          ████  ████          ██            ████    
                ████      ████            ████      ████          ██    ████████████  ██████████████████    
                ████      ████            ████      ████          ████  ████            ████    ████        
                ████      ████            ████      ████        ██████  ████          ████        ████      
                ████      ████████████████████      ████        ████████████      ██████            ████    
                ████      ████                      ████        ██    ██████      ████                ██    
                ████                          ██████████      ████      ██████████████████████████████████  
                ████                        ██████████        ████            ████████████████████████████  
                  ██                                                                                        
{data}                                                                                                                         
                                                                                                                         
""")
    sleep(1)
LEVEL2SPLASH={
    Level.Beginner:"""
                                                                                                                          
                                                                                                                          
                                    ██                              ██                                                    
                                    ██    ████████████████        ████    ████████████                                    
                                    ██          ██    ████      ████  ██    ██      ██                                    
                              ████████████      ██    ████      ██  ████    ██      ██                                    
                                      ████      ██    ████        ████      ████  ██                                      
                                    ████        ██    ████        ██    ██  ████  ██████                                  
████████████████████████            ██  ██      ██    ████    ████████████  ████      ██      ████████████████████████████
                                  ████████    ████    ████    ████████  ██████  ██    ██                                  
                              ████████████    ████    ████          ████    ██  ██  ████                                  
                              ██    ██  ████  ██      ████      ██  ██████  ██    ████                                    
                                    ██        ██      ████    ████  ██  ██████    ████                                    
                                    ██      ████      ██      ████  ██    ██    ████████                                  
                                    ██    ████        ██      ██    ██  ████  ████    ████                                
                                    ██  ████    ████████            ██  ██  ████        ██                                
                                                                                                                          
                                                                                                                          
""",
    Level.Intermediate:"""
                                                                                                                          
                                                                                                                          
                                          ████                      ██                                                    
                                          ████                    ████    ████████████                                    
                                          ████                  ████  ██    ██      ██                                    
                                ████████████████████████        ██  ████    ██      ██                                    
                                ██        ████        ██          ████      ████  ██                                      
                                ██        ████        ██          ██    ██  ████  ██████                                  
████████████████████████        ██        ████        ██      ████████████  ████      ██      ████████████████████████████
                                ██        ████        ██      ████████  ██████  ██    ██                                  
                                ████████████████████████            ████    ██  ██  ████                                  
                                ██        ████        ██        ██  ██████  ██    ████                                    
                                          ████                ████  ██  ██████    ████                                    
                                          ████                ████  ██    ██    ████████                                  
                                          ████                ██    ██  ████  ████    ████                                
                                          ████                      ██  ██  ████        ██                                
                                                                                                                          
                                                                                                                          
""",
    Level.Advanced:"""
                                                                                                                          
                                                                                                                          
                                                                    ██                                                    
                                          ██                      ████    ████████████                                    
                                          ██                    ████  ██    ██      ██                                    
                                          ██                    ██  ████    ██      ██                                    
                                          ██                      ████      ████  ██                                      
                                          ██████████████          ██    ██  ████  ██████                                  
████████████████████████                  ██                  ████████████  ████      ██      ████████████████████████████
                                          ██                  ████████  ██████  ██    ██                                  
                                          ██                        ████    ██  ██  ████                                  
                                          ██                    ██  ██████  ██    ████                                    
                                          ██                  ████  ██  ██████    ████                                    
                                          ██                  ████  ██    ██    ████████                                  
                              ████████████████████████████    ██    ██  ████  ████    ████                                
                                                                    ██  ██  ████        ██                                
                                                                                                                          
                                                                                                                          
""",
}
def show_level(level:Level):
    print(LEVEL2SPLASH[level])
    sleep(1)

def play(session:Session):
    while True:
        dif = configure(dif_orig:=config.difficulty,"メニューに戻る")
        if dif is None:
            return True
        questions=session.get_questions(dif)
        if questions is None:
            print("タイムアウト等により、自動的にログアウトされました。")
            if ask_yes_no("再ログインしますか","再ログインする","再ログインをせず、メニューに戻る"):
                for _ in range(20):
                    if session.relogin():
                        break
                else:
                    print("繰り返し再ログインに失敗したため、再ログインを諦めます。")
                    return False
                continue
            else:
                return False
        if isinstance(dif, Difficulty):
            dif=CustomDifficulty(*DIF2NUMS[dif])
        (score,time)=(0,0)
        if dif.level_strategy==0:
            show_level(Level.Beginner)
            NORMAL_INDEX=dif.easy_num
            HARD_INDEX=NORMAL_INDEX+dif.normal_num
            for i,question in enumerate(questions):
                if i==NORMAL_INDEX:
                    show_level(Level.Intermediate)
                elif i==HARD_INDEX:
                    show_level(Level.Advanced)
                (score_,time_)=ask_question(question,dif)
                score+=score_
                time+=time_
        else:
            for question in questions:
                (score_,time_)=ask_question(question,dif)
                score+=score_
                time+=time_
        if not session.end_try(score,time):
            print("タイムアウト等により、自動的にログアウトされました。")
            if ask_yes_no("再ログインしますか","再ログインする","再ログインをせず、メニューに戻る"):
                for _ in range(20):
                    if session.relogin():
                        break
                else:
                    print("繰り返し再ログインに失敗したため、再ログインを諦めます。")
                    return False
                continue
            else:
                return False
        break
    print(f"結果: {score}点, {time/1000000000}秒")
    if isinstance(dif_orig,CustomDifficulty):
        return True
    while True:
        rank=session.get_rank(dif_orig)
        if rank is None:
            print("タイムアウト等により、自動的にログアウトされました。")
            if ask_yes_no("再ログインしますか","再ログインする","再ログインをせず、メニューに戻る"):
                for _ in range(20):
                    if session.relogin():
                        break
                else:
                    print("繰り返し再ログインに失敗したため、再ログインを諦めます。")
                    return False
                continue
            else:
                return False
        ranking=session.get_ranking(dif_orig, rank-5,rank+5)
        if ranking is None:
            print("タイムアウト等により、自動的にログアウトされました。")
            if ask_yes_no("再ログインしますか","再ログインする","再ログインをせず、メニューに戻る"):
                for _ in range(20):
                    if session.relogin():
                        break
                else:
                    print("繰り返し再ログインに失敗したため、再ログインを諦めます。")
                    return False
                continue
            else:
                return False
        max_rank_width=max(len(str(i.rank))for i in ranking)
        print("ランキング: ")
        for i in ranking:
            rank=str(i.rank).ljust(max_rank_width)
            print(f"{rank}位:{i.user_name} ({i.score}点, {i.time_in_ns/1000000000}秒)")
        sleep(10)
        return True
    
def ask_question(question:Question,dif:CustomDifficulty)->tuple[int,int]:
    data=""
    for _ in [0]:
        if True or dif.level_strategy==1:
            data+="レベル: "+LEVEL_NAMES[question.level]
        if dif.show_level==0:
            break
        data+="\n大分類: "+question.category
        if dif.show_level==1:
            break
        data+="\n小分類: "+question.subcategory
        if dif.show_level==2:
            break
        data+="\nキーワード: "+question.keyword
    show_mondai(data)
    question_text = question.sentence 
    matches = [*RE_ANSWER.finditer(question_text)]
    answers:list[str] = []
    for match in matches:
        question_text=question_text[:match.start()]+"["+"_"*(len(match[1]))+"]"+question_text[match.end():]
        answers.append(match[1])
    print("以下の[___]に入る語句を答えなさい:" if len(answers)==1 else "以下の[___]に入る語句をTab区切りで答えなさい:\n")
    print(question_text)
    print("訳: "+question.japanese_translation)
    print()
    time_start=monotonic_ns()
    res=input("回答: ").split("¥t")
    time=monotonic_ns()-time_start
    time_req=TIME_PROPO_FACTOR*sum(len(i)for i in answers)+TIME_CONST_FACTOR
    if answers==res:
        print("正解!")
        print()
        score=10
        score-=min(2,time//time_req)
        print(f"点数: {score}/10")
        print(f"秒数: {time/1000000000}/{time_req/1000000000}")
        sleep(1)
        return (score,time)
    else:
        print("不正解: "+RE_ANSWER.sub(r"[\1]",question.sentence))
        print()
        print(f"点数: 0/10")
        print(f"秒数: {time/1000000000}/{time_req/1000000000}")
        sleep(3)
        return (0,time)