from aiogram.fsm.state import State, StatesGroup

class OrderForm(StatesGroup):
    """Форма заявки"""
    waiting_for_measurements = State()                    
    waiting_for_name = State()       
    waiting_for_phone = State()           
    waiting_for_photo = State()                      
    confirmation = State()                 


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_broadcast = State()                                   


class QuizForm(StatesGroup):
    """Квиз для подбора мебели"""
    question_1_room = State()                                       
    question_2_style = State()                                  
    question_2_kitchen_style = State()                                                             
    question_3_type = State()                                       
    question_3_material = State()                                                          
    question_4_finish = State()                                        
    question_4_price = State()                                                        
    question_5_features = State()                                                                              
    viewing_results = State()                              


class QuizOrderForm(StatesGroup):
    """Форма заявки из квиза (только имя и телефон)"""
    waiting_for_name = State()       
    waiting_for_phone = State()           
    confirmation = State()                 
