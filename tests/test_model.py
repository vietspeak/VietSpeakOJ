from model.model import User

class test_generate_password():
    s_1 = User.generate_password()
    assert len(s_1) == 10
    s_2 = User.generate_password(25)
    assert len(s_2) == 25