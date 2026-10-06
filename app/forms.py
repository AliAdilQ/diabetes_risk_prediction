"""Shared WTForms validation for browser forms and the JSON endpoint."""

import math

from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import InputRequired, Length, NumberRange, StopValidation

from .features import FEATURES


def finite_number(form, field):
    try:
        valid = field.data is not None and math.isfinite(field.data)
    except OverflowError:
        valid = False
    if not valid:
        raise StopValidation("Enter a finite number.")


class PredictionForm(FlaskForm):
    submit = SubmitField("Estimate risk")


for feature in FEATURES:
    field_type = IntegerField if feature.integer else FloatField
    setattr(PredictionForm, feature.key, field_type(
        feature.label,
        validators=[InputRequired(), finite_number, NumberRange(feature.minimum, feature.maximum)],
        render_kw={"min": feature.minimum, "max": feature.maximum,
                   "step": "1" if feature.integer else "any", "placeholder": feature.example},
    ))


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[InputRequired(), Length(max=256)])
    submit = SubmitField("Sign in to workspace")


class ActionForm(FlaskForm):
    """CSRF token used for logout and record deletion."""

    submit = SubmitField("Confirm")
