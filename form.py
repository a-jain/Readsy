from flask_wtf import Form
from wtforms import TextField, widgets, RadioField, validators
from wtforms.fields import SelectMultipleField
from wtformsparsleyjs import StringField, SelectField

import pycountry

class TextSelect(Form):
	texts=[("http://readsy.co/static/txt/ironman.html", "Iron Man"), ("http://readsy.co/static/txt/gulls.html", "Gulls")]
	textChooser = SelectMultipleField('Text to be Spritzed', choices=texts)

class UserSurvey1(Form):
	age = [("u10", "Under 10"), ("11-20", "11-20"), ("21-40", "21-40"), ("41-60", "41-60"), ("61-80", "61-80"), ("81+", "Over 81")]
	allDifficulties = [("AMD", "Age Related Macular Degeneration"), ("BI", "Brain Injury"), ("D", "Dyslexia"), ("VI", "Vision Issues"), ("O", "Other"), ("N", "None")]
	nativelang = [("yes", "Yes"), ("no", "No")]
	device = [("desktop", "Desktop"), ("laptop", "Laptop"), ("tablet", "Tablet"), ("mobile", "Smartphone")]

	cc = {}
	t = list(pycountry.countries)
	for country in t:
		cc[country.name]=country.name
	cc = [(v, v) for v, v in cc.iteritems()]
	cc.sort()
	cc.insert(0, (None, ""))
	age.insert(0, (None, ""))
	country = SelectField('Country', [validators.DataRequired(message='Sorry, this is a required field.')], choices=cc)
	agerange = SelectField('Age Range', [validators.DataRequired(message='Sorry, this is a required field.')], choices=age)
	difficulties = SelectMultipleField('Reading Difficulties (select all that apply)', [validators.DataRequired(message='Sorry, this is a required field.')], choices=allDifficulties, coerce=unicode, option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
	nativelang = RadioField('Is English your native language?', [validators.DataRequired(message='Sorry, this is a required field.')], choices=nativelang)
	deviceused = RadioField('What device are you using?', [validators.DataRequired(message='Sorry, this is a required field.')], choices=device)

	aq1_label = "How tall was the Iron Man?"
	aq2_label = "His eyes were like?"
	aq3_label = "What flew over and landed?"
	aq4_label = "What did they have on the cliff?"
	aq5_label = "What did the seagull pick up first?"
	aq1_answers = [("a", "very tall"), ("b", "short"), ("c", "taller than a house"), ("d", "taller than a boulder")]
	aq2_answers = [("a", "headlamps"), ("b", "rocks"), ("c", "cats"), ("d", "flames")]
	aq3_answers = [("a", "a hummingbird"), ("b", "a bat"), ("c", "two seagulls"), ("d", "a plane")]
	aq4_answers = [("a", "a houseboat"), ("b", "two chicks in a nest"), ("c", "a nest"), ("d", "a drum of oil")]
	aq5_answers = [("a", "nothing"), ("b", "a finger"), ("c", "a knife blade"), ("d", "one of the Iron Man's eyes")]
	aq1 = RadioField(aq1_label, choices=aq1_answers)
	aq2 = RadioField(aq2_label, choices=aq2_answers)
	aq3 = RadioField(aq3_label, choices=aq3_answers)
	aq4 = RadioField(aq4_label, choices=aq4_answers)
	aq5 = RadioField(aq5_label, choices=aq5_answers)

	bq1_label = "What did the second seagull pickup?"
	bq2_label = "What color did the eye glow?"
	bq3_label = "What did the Iron Man try to pick up, stuck between the rocks?"
	bq4_label = "What was the eye doing when they found it?"
	bq5_label = "How did the legs move?"
	bq1_answers = [("a", "a clam"), ("b", "the right hand"), ("c", "a house"), ("d", "bridseed")]
	bq2_answers = [("a", "blue"), ("b", "purple"), ("c", "white"), ("d", "pink")]
	bq3_answers = [("a", "a hummingbird"), ("b", "the left arm"), ("c", "two seagulls"), ("d", "a plane")]
	bq4_answers = [("a", "waving"), ("b", "blinking at them"), ("c", "sleeping"), ("d", "nothing")]
	bq5_answers = [("a", "running"), ("b", "skip"), ("c", "with a limp"), ("d", "Hop, hop, hop, hop")]
	bq1 = RadioField(bq1_label, choices=bq1_answers)
	bq2 = RadioField(bq2_label, choices=bq2_answers)
	bq3 = RadioField(bq3_label, choices=bq3_answers)
	bq4 = RadioField(bq4_label, choices=bq4_answers)
	bq5 = RadioField(bq5_label, choices=bq5_answers)