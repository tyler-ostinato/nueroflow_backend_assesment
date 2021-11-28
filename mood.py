from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from datetime import timedelta
import ast

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mood.db'
db = SQLAlchemy(app)


# Store list of moods for a user by date
class MoodList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default = datetime.strftime(datetime.today(), "%b %d %Y"))
    mood = db.Column(db.String(20)) # happy, sad, angry

    def __repr__(self):
        return f"['{self.date}', '{self.user}', '{self.mood}']"


@app.route('/mood')
def find_mood():
    user = request.args.get('user')
    # grab entries of the current logged in user
    moods = MoodList.query.filter_by(user=user)

    # add moods to a running list
    mood_data = []
    # get the current streak of user
    date_list = []
    for mood in moods:
        entry_as_list = ast.literal_eval(repr(mood))
        mood_entry = {"Date":entry_as_list[0], "Mood":entry_as_list[2]}
        mood_data.append(mood_entry)
        # get list of days a mood was set
        date = datetime.fromisoformat(entry_as_list[0]).toordinal()
        date_list.append(date)

    count=1
    streaks = []
    # Avoid IndexError for  random_list[i+1]
    for i in range(len(date_list) - 1):
        # Check if the next number is consecutive
        if date_list[i] + 1 == date_list[i+1]:
            count += 1
        else:
            # If it is not append the count and restart counting
            streaks.append(count)
            count = 1
    # Since we stopped the loop one early append the last count
    streaks.append(count)


    # return all the entries
    return {
            user:{
                "streak":streaks[-1],
                "mood_data":mood_data
            }
}

@app.route('/mood', methods=['POST'])
def add_mood():
    # post a new mood submitted by the user
    mood = MoodList(date=datetime.now().date()+timedelta(days=40), user=request.json['user'], mood=request.json['mood'])
    db.session.add(mood)
    db.session.commit()
    return {"Date":datetime.now(), "Mood":mood.mood}


if __name__ == '__main__':
    app.run(debug=True)
