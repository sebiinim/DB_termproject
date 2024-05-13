from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sebin'

connect = psycopg2.connect("dbname=termproject user=postgres password=sebin")
cur = connect.cursor()


@app.route('/')
def loginmain():
  return render_template("signin.html")

@app.route('/signin', methods=['POST'])
def signin():
  id = request.form["id"]
  password = request.form["password"]

  cur.execute("SELECT * FROM users WHERE id = %s AND password = %s", (id, password))
  isRegisteredUser = cur.fetchone()

  if isRegisteredUser and len(id)>0 and len(password)>0:
    session['id'] = request.form['id']
    return redirect(url_for('mainpage'))
  else:
    return render_template("signin_fail.html", isRegisteredUser=isRegisteredUser)
  
@app.route('/signup', methods=['POST'])
def signup():
  id = request.form["id"]
  password = request.form["password"]
  
  cur.execute("SELECT id FROM users WHERE id = %s", (id,))
  isRegisteredId = cur.fetchone()
  
  if isRegisteredId or len(id)< 1 or len(password) < 1:
    return render_template("signup_fail.html", isRegisteredId=isRegisteredId)
  else:
    cur.execute("insert into users (id, password, role) values (%s, %s, 'user')", (id, password))
    connect.commit()
    return redirect(url_for('loginmain'))
  
@app.route('/logout')
def logout():
  session.pop('user_id', None)
  return redirect(url_for('loginmain'))

  
@app.route('/main', methods=['GET', 'POST'])
def mainpage():
  #유저 정보 세션
  user_id = session['id']
  
  #cur.execute("SELECT * FROM movies ORDER BY rel_date DESC;")
  if request.method == 'POST':
    sort_by1 = request.form.get('sort_by1')
    if sort_by1 == 'latest':
      cur.execute("SELECT m.id, m.title, m.director, m.genre, m.rel_date, trunc(AVG(r.ratings),1) AS ratings \
        FROM movies m JOIN reviews r ON m.id = r.mid GROUP BY m.id, m.title, m.director, m.genre, m.rel_date\
        ORDER BY rel_date DESC;")
    elif sort_by1 == 'genre':
      cur.execute("SELECT m.id, m.title, m.director, m.genre, m.rel_date, trunc(AVG(r.ratings),1) AS ratings \
        FROM movies m JOIN reviews r ON m.id = r.mid GROUP BY m.id, m.title, m.director, m.genre, m.rel_date\
        ORDER BY genre;")  
    else:
      cur.execute("SELECT m.id, m.title, m.director, m.genre, m.rel_date, trunc(AVG(r.ratings),1) AS ratings \
        FROM movies m JOIN reviews r ON m.id = r.mid GROUP BY m.id, m.title, m.director, m.genre, m.rel_date\
        order by ratings DESC;") 
  result1 = cur.fetchall()
  
  #cur.execute("SELECT * from movies, reviews where movies.id = reviews.mid ORDER BY rev_time DESC;")
  if request.method == 'POST':
    sort_by2 = request.form.get('sort_by2')
    if sort_by2 == 'latest':
      cur.execute("with subquery as ( \
        SELECT u.id, COALESCE(f.followers_count, 0) AS followers_count\
        FROM users u LEFT JOIN ( \
        SELECT opid, COUNT(*) AS followers_count\
        FROM ties WHERE tie = 'follow' GROUP BY opid) f ON u.id = f.opid)\
        select ratings, title, director, genre, rel_date, mid, uid, m.id, review, rev_time, s.followers_count\
        from movies m, reviews r, subquery s where m.id = r.mid and r.uid = s.id\
        group by uid, m.id, r.mid, s.followers_count ORDER BY rev_time DESC;")
    elif sort_by2 == 'title':
      cur.execute("with subquery as ( \
        SELECT u.id, COALESCE(f.followers_count, 0) AS followers_count\
        FROM users u LEFT JOIN ( \
        SELECT opid, COUNT(*) AS followers_count\
        FROM ties WHERE tie = 'follow' GROUP BY opid) f ON u.id = f.opid)\
        select ratings, title, director, genre, rel_date, mid, uid, m.id, review, rev_time, s.followers_count\
        from movies m, reviews r, subquery s where m.id = r.mid and r.uid = s.id\
        group by uid, m.id, r.mid, s.followers_count ORDER BY title;") 
    else:
      cur.execute(" with subquery as ( \
        SELECT u.id, COALESCE(f.followers_count, 0) AS followers_count\
        FROM users u LEFT JOIN ( \
        SELECT opid, COUNT(*) AS followers_count\
        FROM ties WHERE tie = 'follow' GROUP BY opid) f ON u.id = f.opid)\
        select ratings, title, director, genre, rel_date, mid, uid, m.id, review, rev_time, s.followers_count\
        from movies m, reviews r, subquery s where m.id = r.mid and r.uid = s.id\
        group by uid, m.id, r.mid, s.followers_count order by s.followers_count DESC ")
  result2 = cur.fetchall()
  
  return render_template("main.html", movies=result1, reviews=result2, user_id = user_id)

@app.route('/movie_detail/<string:movie_id>')
def movie_detail(movie_id):
  user_id = session['id']
  
  cur.execute("select director, genre, rel_date, title, id from movies where id = %s", (movie_id,))
  result1 = cur.fetchone()
  
  cur.execute("SELECT ratings, uid, review, rev_time from reviews \
    where reviews.mid = %s ORDER BY review;", (movie_id,))
  result2 = cur.fetchall()
  
  cur.execute("select trunc(avg(ratings),1) from reviews where mid = %s group by mid", (movie_id,))
  result3 = cur.fetchone()
  return render_template("movie_detail.html", movie_detail=result1, movie_reviews=result2, \
    avg_rating=result3, user_id = user_id)

@app.route('/movie_detail_bytitle_redirect/<string:movie_title>')
def movie_detail_bytitle_redirect(movie_title):
  
  cur.execute("SELECT id FROM movies WHERE title = %s", (movie_title,))
  result = cur.fetchone()
  movie_id = result[0]
  return redirect(url_for('movie_detail', movie_id=movie_id))


@app.route('/user_detail/<string:user_id>')  
def user_detail(user_id):
  user_id_session = session['id']
  
  if user_id_session == user_id:
    cur.execute("select uid, ratings, title, review, rev_time FROM user_info, reviews, movies \
      WHERE user_info.id = reviews.uid and reviews.mid = movies.id and reviews.uid = %s order by rev_time DESC", (user_id_session,))
    result1 = cur.fetchall()
    
    cur.execute("select id from ties where opid = %s and tie = 'follow'", (user_id_session,))
    result2 = cur.fetchall()
    
    cur.execute("select opid from ties WHERE id = %s and tie = 'follow'", (user_id_session,))
    result3 = cur.fetchall()
    
    cur.execute("select opid from ties WHERE id = %s and tie = 'mute'", (user_id_session,))
    result4 = cur.fetchall()
    
    if user_id_session in ['admin', 'admin2']:
      return render_template("mypage_admin.html", user_detail = result1, user_id = user_id_session)
    
    else:
      return render_template("mypage.html", user_detail = result1, user_id = user_id_session \
        ,followed = result2, following = result3, muting = result4)
      
  else:
    cur.execute("select uid, ratings, title, review, rev_time FROM user_info, reviews, movies \
      where user_info.id = reviews.uid and reviews.mid = movies.id and reviews.uid = %s order by rev_time DESC", (user_id,))
    result1 = cur.fetchall()
    return render_template("user_detail.html", user_detail = result1, user_id = user_id_session)

#Follow or Mute
@app.route('/follow_user/<string:user_id>')
def follow_user(user_id):
    user_id_session = session['id']  # 현재 로그인한 사용자의 ID

    # 이미 mute 관계가 존재하는지 확인
    cur.execute("SELECT * FROM ties WHERE id = %s AND opid = %s AND tie = 'mute'", (user_id_session, user_id))
    existing_mute_relationship = cur.fetchone()

    if existing_mute_relationship:
        # mute 관계를 삭제
        cur.execute("DELETE FROM ties WHERE id = %s AND opid = %s AND tie = 'mute'", (user_id_session, user_id))
        connect.commit()

    # 이미 팔로우 관계가 존재하는지 확인
    cur.execute("SELECT * FROM ties WHERE id = %s AND opid = %s AND tie = 'follow'", (user_id_session, user_id))
    existing_follow_relationship = cur.fetchone()

    if existing_follow_relationship:
        # 이미 존재하는 관계이므로 중복 삽입을 막기 위해 아무 작업도 하지 않고 리디렉션
        return redirect(url_for('user_detail', user_id=user_id))
    else:
        # 팔로우 관계를 삽입
        cur.execute("INSERT INTO ties (id, opid, tie) VALUES (%s, %s, 'follow')", (user_id_session, user_id))
        connect.commit()
        return redirect(url_for('user_detail', user_id=user_id))

@app.route('/mute_user/<string:user_id>')
def mute_user(user_id):
    user_id_session = session['id']  # 현재 로그인한 사용자의 ID

    # 이미 follow 관계가 존재하는지 확인
    cur.execute("SELECT * FROM ties WHERE id = %s AND opid = %s AND tie = 'follow'", (user_id_session, user_id))
    existing_follow_relationship = cur.fetchone()

    if existing_follow_relationship:
        # follow 관계를 삭제
        cur.execute("DELETE FROM ties WHERE id = %s AND opid = %s AND tie = 'follow'", (user_id_session, user_id))
        connect.commit()

    # 이미 mute 관계가 존재하는지 확인
    cur.execute("SELECT * FROM ties WHERE id = %s AND opid = %s AND tie = 'mute'", (user_id_session, user_id))
    existing_mute_relationship = cur.fetchone()

    if existing_mute_relationship:
        # 이미 존재하는 관계이므로 중복 삽입을 막기 위해 아무 작업도 하지 않고 리디렉션
        return redirect(url_for('user_detail', user_id=user_id))
    else:
        # mute 관계를 삽입
        cur.execute("INSERT INTO ties (id, opid, tie) VALUES (%s, %s, 'mute')", (user_id_session, user_id))
        connect.commit()
        return redirect(url_for('user_detail', user_id=user_id))

@app.route('/unfollow_user/<string:user_id>')
def unfollow_user(user_id):
  user_id_session = session['id']  # 현재 로그인한 사용자의 ID

  # 이미 팔로우 관계가 존재하는지 확인
  cur.execute("SELECT * FROM ties WHERE id = %s AND opid = %s AND tie = 'follow'", (user_id_session, user_id))
  existing_follow_relationship = cur.fetchone()

  if existing_follow_relationship:
    # 팔로우 관계를 삭제
    cur.execute("DELETE FROM ties WHERE id = %s AND opid = %s AND tie = 'follow'", (user_id_session, user_id))
    connect.commit()
        
  cur.execute("select uid, ratings, title, review, rev_time FROM user_info, reviews, movies \
      WHERE user_info.id = reviews.uid and reviews.mid = movies.id and reviews.uid = %s order by rev_time DESC", (user_id_session,))
  result1 = cur.fetchall()
    
  cur.execute("select opid from ties WHERE id = %s and tie = 'follow'", (user_id_session,))
  result2 = cur.fetchall()
    
  cur.execute("select opid from ties WHERE id = %s and tie = 'mute'", (user_id_session,))
  result3 = cur.fetchall()
    
  return redirect(url_for('user_detail', user_id = user_id_session))

@app.route('/unmute_user/<string:user_id>')
def unmute_user(user_id):
  user_id_session = session['id']  # 현재 로그인한 사용자의 ID

  cur.execute("SELECT * FROM ties WHERE id = %s AND opid = %s AND tie = 'mute'", (user_id_session, user_id))
  existing_follow_relationship = cur.fetchone()

  if existing_follow_relationship:
    cur.execute("DELETE FROM ties WHERE id = %s AND opid = %s AND tie = 'mute'", (user_id_session, user_id))
    connect.commit()
        
  cur.execute("select uid, ratings, title, review, rev_time FROM user_info, reviews, movies \
      WHERE user_info.id = reviews.uid and reviews.mid = movies.id and reviews.uid = %s order by rev_time DESC", (user_id_session,))
  result1 = cur.fetchall()
    
  cur.execute("select opid from ties WHERE id = %s and tie = 'follow'", (user_id_session,))
  result2 = cur.fetchall()
    
  cur.execute("select opid from ties WHERE id = %s and tie = 'mute'", (user_id_session,))
  result3 = cur.fetchall()
    
  return redirect(url_for('user_detail', user_id = user_id_session))
  
from datetime import datetime

@app.route('/submit_review', methods=['POST'])
def submit_review():
  if request.method == 'POST':
    mid = request.args.get('mid')
    uid = request.args.get('uid')
    ratings = int(request.form['rating'])
    review = request.form['review']
    rev_time = datetime.now()

    # 해당 사용자가 이미 작성한 리뷰가 있는지 확인
  cur.execute("SELECT * FROM reviews WHERE mid = %s AND uid = %s", (mid, uid))
  existing_review = cur.fetchone()

  if existing_review:
    # 이미 작성한 리뷰가 있으면 삭제
    cur.execute("DELETE FROM reviews WHERE mid = %s AND uid = %s", (mid, uid))
    connect.commit()

  # 새 리뷰 삽입
  cur.execute("INSERT INTO reviews (mid, uid, ratings, review, rev_time) VALUES (%s, %s, %s, %s, %s)", \
    (mid, uid, ratings, review, rev_time))
  connect.commit()

  return redirect(url_for('movie_detail', movie_id=mid))

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
  user_id_session = session['id']
  
  if request.method == 'POST':
    cur.execute("SELECT COUNT(*) FROM movies")
    row_count = cur.fetchone()[0]
    
    id = row_count + 1    
    title = request.form['title']
    director = request.form['director']
    genre = request.form['genre']
    release_date = request.form['release_date']

    # movies 테이블에 데이터 삽입
    cur.execute("INSERT INTO movies (id, title, director, genre, rel_date) VALUES (%s, %s, %s, %s, %s)",
                (id, title, director, genre, release_date))
    connect.commit()

  cur.execute("select uid, ratings, title, review, rev_time FROM user_info, reviews, movies \
      WHERE user_info.id = reviews.uid and reviews.mid = movies.id and reviews.uid = %s order by rev_time DESC", (user_id_session,))
  result1 = cur.fetchall()
    
  return render_template("mypage_admin.html", user_detail = result1, user_id = user_id_session)



if __name__ == '__main__':
  app.run(port=8000, debug=True)
