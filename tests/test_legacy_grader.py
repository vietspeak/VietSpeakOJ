from grader.grading_transcript import LegacyGrader
from utils.dictionary import Dictionary
from pytest import fixture


@fixture
def grader(dictionary: Dictionary) -> LegacyGrader:
    return LegacyGrader(dictionary)


def test_legacy_grader(grader: LegacyGrader):
    grading_result = grader.grader(
        "A very good morning teacher", "A really good morning teacher"
    )
    assert abs(grading_result.score - 8 / 9) < 1e-6
    assert grading_result.errors == [("REALLY", "VERY")]


def test_scenario_1(grader: LegacyGrader):
    grading_result = grader.grader(
        """
    every time you decide not to speak not to express your thoughts because it's not fully articulated because every time you say no to an interview or a job offer or an invitation because it requires english and you are just not sure if your english is good enough or you're just afraid to speak, then your biggest enemy is winning. And you are losing. This is failure, not trying to say something and making a mistake, not saying something and getting stuck, That's not failing, that's just practicing. That's just living. Even if the speakers make mistakes, okay then it's like and then it's okay and that's your native tongue. Stop being so judgmental. Let go lose this idea of the fiction. Stop feeding the monster. Because then you are the only person who is gonna pay the price. Let's say you're in a meeting and just sitting there and you have something to say, but you don't say it because there is a word in it that has an R. And you are not sure how to say it or you know how to start with, you are not sure how to finish and you keep quiet what's going to happen? Who's losing from this situation? You are? Who's screening everyone else? They're shining, They're expressing their toss their advancing. If you don't speak up, if you don't speak out your toss your opinions, your heart, then you say stay behind. Now look, I'm a non native speaker and I know what it's like. I judge myself all the time. I always listen to myself from the outside and I'm like, you make a mistake there. that wasn't good enough. But had I let this affect me and control me, I would have never make made so many videos teaching you. I would have never had a Youtube general. I would have never succeeded as the speech coach as an english coach because I don't care about that. I don't care about the mistakes I make. I mean sometimes I get a comment and I get offended a little bit and it was like, I get all defensive, but that's last, I don't know, two seconds. And then I'm like that, I don't care like a large majority of my students and my flowers appreciate what I have to say and they respect me and that's what matters. And it's the same thing for you. People are more interested in what you have to say then in the mistakes that you're making and if you come across a person who makes fun of you, who is judging you, who gives pointing out at all your mistakes, that maybe this person shouldn't be around you. Maybe they're not a good friend. So think about it. Just the person who used route yourself with you, only want people who support you, who empowered you and who encouraged you
    """,
        """
    EVERY TIME DECIDE SPEAK EXPRESS YOUR THOUGHTS BECAUSE FULLY ARTICULATED BECAUSE EVERY TIME INTERVIEW OFFER INVITATION BECAUSE REQUIRES ENGLISH JUST SURE YOUR ENGLISH GOOD ENOUGH JUST AFRAID SPEAK THEN BIGGEST ENEMY WINNING LOSING THIS FAILURE TRYING SOMETHING MAKING MISTAKE SAYING SOMETHING GETTING STUCK FAILING JUST PRACTICING JUST LIVING EVEN NATIVE SPEAKERS MAKE MISTAKES OKAY THEN OKAY BECAUSE NATIVE STOP BEING LOSE THIS IDEA PERFECTION STOP FEEDING MONSTER BECAUSE THEN ONLY PERSON GOING PRICE MEETING SITTING THERE HAVE SOMETHING BECAUSE THERE WORD THAT SURE KNOW START SURE FINISH KEEP QUIET HAPPEN LOSING FROM THIS SITUATION WINNING EVERYONE ELSE SHINING EXPRESSING THEIR THOUGHTS ADVANCING SPEAK SPEAK YOUR THOUGHTS YOUR OPINIONS YOUR HEART THEN STAY BEHIND LOOK SPEAKER KNOW WHAT LIKE JUDGE MYSELF TIME ALWAYS MYSELF FROM OUTSIDE LIKE MADE MISTAKE HERE THAT GOOD ENOUGH THIS AFFECT CONTROL NEVER MADE MANY VIDEOS TEACHING NEVER CHANNEL NEVER SUCCEEDED SPEECH COACH ENGLISH COACH BECAUSE CARE ABOUT THAT CARE ABOUT MISTAKES MAKE MEAN SOMETIMES COMMENT OFFENDED LITTLE KNOW SECONDS THEN LIKE THAT LARGE MAJORITY STUDENTS FOLLOWERS APPRECIATE WHAT HAVE THEY RESPECT WHAT MATTERS SAME THING PEOPLE MORE INTERESTED WHAT HAVE MISTAKES THAT MAKING COME ACROSS PERSON MAKES JUDGING KEEPS POINTING YOUR MISTAKES THEN MAYBE THAT PERSON AROUND GOOD FRIEND THINK ABOUT CHOOSE PEOPLE SURROUND YOURSELF WITH ONLY WANT PEOPLE SUPPORT EMPOWER ENCOURAGE
    """,
    )
    assert ("ENCOURAGE", "ENCOURAGED") in grading_result.errors
    assert ("PERFECTION", "FICTION") in grading_result.errors
    assert grading_result.score <= 1


def test_scenario_2(grader: LegacyGrader):
    student_text = """
    stretching along the coast of southeast asia with dense mountains and jungles to the west. 
the socialist republic of vietnam is home to approximately 100 million people. 
vietnam's history has been shaped through its jar of the maritime trade as well as this tumultuous relationship with its neighbor china to the north. 
since prehistoric times, 
vietnam's red river delta has been a population center due to its fertile soil and defensible location, 
feudal communities of rice growers began to develop in this region and eventually confederated to form the kingdom of england, 
which corresponds to the bronze age dongshan material culture. 
along the southern coast, 
a separate south and seafaring culture developed strong ties with the western central philippine archipelago. 
the likely people of england united with the you people namgung too formal. 
like in 57 bc the engine new people are the ancestors of modern high speaking peoples of northern vietnam, 
such as the short hair tattoos in the practice of teeth blackening rural cultural aspects originating with the u. 
alec had a significant uniting influence. 
however, it only lasted the one long range of this founding monarch. 
in response to the first chinese emperor qin shi huang and his successors expansion southwards, 
the many you tribes in the region united and formed a powerful kingdom of nan you which became wealthy through the exportation of ivory, 
pearls and precious woods from the jungles of vietnam as china reunited under the han dynasty, 
they began to extract tribute from nan you. 
eventually this was not enough to satisfy the han emperor nanu was invaded and incorporated into the han empire. 
han chinese rule was marked with failed attempts to assimilate the populace into the larger homogenized chinese culture, 
particularly with common women who enjoy far greater autonomy and cultural status than their chinese counterparts. 
at the time. in 40 82, daughters of a military prefect rebelled after one of their husbands was executed by the han, 
the transistors ambushed a small local garrison of their village and began taking othe
r cities and towns. 
the chinese did not initially take the rebellion seriously and responded in competently and were defeated time and again by the sisters, 
who had raised an army of 80,000, 
including a sizeable number of women and villagers whom they had trained.
    """

    grader_text = """
    STRETCHING ALONG COAST ASIA WITH DENSE SOCIALIST REPUBLIC VIETNAM HOME APPROXIMATELY PEOPLE HISTORY BEEN SHAPED THROUGH GEOGRAPHY MARITIME TRADE TUMULTUOUS RELATIONSHIP WITH NEIGHBOR CHINA NORTH SINCE PREHISTORIC TIMES RIVER DELTA BEEN POPULATION CENTER FERTILE SOIL LOCATION COMMUNITIES RICE GROWERS BEGAN DEVELOP THIS REGION EVENTUALLY KINGDOM WHICH CORRESPONDS BRONZE MATERIAL CULTURE ALONG SOUTHERN COAST SEPARATE CULTURE DEVELOPED STRONG TIES WITH WESTERN CENTRAL PHILIPPINE ARCHIPELAGO PEOPLE UNITED WITH PEOPLE ANCIENT PEOPLE ANCESTORS MODERN SPEAKING PEOPLES NORTHERN VIETNAM SUCH HAIR TATTOOS PRACTICE TEETH CULTURAL ASPECTS ORIGINATING WITH SIGNIFICANT UNITING INFLUENCE HOWEVER ONLY LASTED LONG REIGN FOUNDING MONARCH RESPONSE FIRST CHINESE EMPEROR SUCCESSORS EXPANSION MANY TRIBES REGION UNITED POWERFUL KINGDOM WHICH BECAME WEALTHY THROUGH IVORY PEARLS PRECIOUS WOODS FROM JUNGLES VIETNAM CHINA REUNITED DYNASTY THEY BEGAN EXTRACT TRIBUTE FROM EVENTUALLY THIS ENOUGH SATISFY INVADED INCORPORATED EMPIRE CHINESE RULE MARKED WITH FAILED ATTEMPTS ASSIMILATE VIET LARGER HOMOGENIZED CHINESE CULTURE PARTICULARLY WITH COMMON WOMEN GREATER AUTONOMY CULTURAL STATUS THAN THEIR CHINESE COUNTERPARTS TIME DAUGHTERS MILITARY PREFECT AFTER THEIR HUSBANDS EXECUTED SISTERS AMBUSHED SMALL LOCAL GARRISON THEIR VILLAGE BEGAN TAKING OTHER CITIES TOWNS CHINESE INITIALLY TAKE REBELLION SERIOUSLY RESPONDED WERE DEFEATED TIME AGAIN SISTERS ARMY INCLUDING SIZABLE NUMBER WOMEN VILLAGERS WHOM THEY TRAINED
    """
    grading_result = grader.grader(student_text, grader_text)
    for pair in grading_result.errors:
        assert pair[1] != "TRAINED"
    assert grading_result.score <= 1