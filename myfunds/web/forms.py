from wtforms import DateTimeField
from wtforms import Form
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import validators as vals
from wtforms.fields.simple import FileField

from myfunds.web import constants


# fmt: off
username_field = lambda: StringField(validators=[vals.InputRequired(), vals.Regexp(r"^[a-zA-Z0-9_]{4,100}$")])  # noqa: E501, E731
password_field = lambda: PasswordField(validators=[vals.InputRequired(), vals.Length(min=6, max=100)])  # noqa: E501, E731
id_field = lambda: IntegerField(validators=[vals.InputRequired(), vals.NumberRange(min=1)])  # noqa: E501, E731
# fmt: on


class LoginForm(Form):
    username = username_field()
    password = password_field()


class AddAccountForm(Form):
    # fmt: off
    username = username_field()
    password = password_field()
    password_copy = PasswordField(validators=[vals.InputRequired(), vals.EqualTo("password")])  # noqa: E501
    # fmt: on


class UpdateAccountPasswordForm(Form):
    # fmt: off
    account_id = id_field()
    old_password = password_field()
    new_password = password_field()
    new_password_copy = PasswordField(validators=[vals.InputRequired(), vals.EqualTo("new_password")])  # noqa: E501
    # fmt: on


class DeleteAccountForm(Form):
    # fmt: off
    account_id = id_field()
    passphrase = StringField(validators=[vals.InputRequired(), vals.Regexp(r"delete this account")])  # noqa: E501
    # fmt: on


class AddCurrencyForm(Form):
    # fmt: off
    code_alpha = StringField(validators=[vals.InputRequired(), vals.Regexp(r"^[a-zA-Z]{3}$")])  # noqa: E501
    precision = IntegerField(validators=[vals.InputRequired(), vals.NumberRange(min=0)])
    # fmt: on


class DeleteCurrencyForm(Form):
    currency_id = id_field()


class AddCategoryForm(Form):
    # fmt: off
    direction = StringField(validators=[vals.InputRequired(), vals.AnyOf(constants.FundsDirection.values())])  # noqa: E501
    name = StringField(validators=[vals.InputRequired()])
    color_sign = StringField(validators=[vals.InputRequired(), vals.Regexp(r"^#[a-f0-9]{6}$")])  # noqa: E501
    # fmt: on


class EditCategoryForm(Form):
    # fmt: off
    category_id = id_field()
    name = StringField(validators=[vals.Optional()])
    color_sign = StringField(validators=[vals.Optional(), vals.Regexp(r"^#[a-f0-9]{6}$")])  # noqa: E501
    # fmt: on


class DeleteCategoryForm(Form):
    category_id = id_field()


class AddBalanceForm(Form):
    # fmt: off
    name = StringField(validators=[vals.InputRequired()])
    currency = StringField(validators=[vals.InputRequired(), vals.Regexp(r"^[A-Z]{3}$")])  # noqa: E501
    # fmt: on


class AddTransactionForm(Form):
    amount = StringField(validators=[vals.InputRequired()])
    category_id = IntegerField(validators=[vals.Optional(), vals.NumberRange(min=1)])
    created_at = DateTimeField(validators=[vals.InputRequired()])
    comment = StringField(validators=[vals.Optional()])


class UpdateTransactionCategoryForm(Form):
    txn_id = id_field()
    category_id = IntegerField(validators=[vals.Optional(), vals.NumberRange(min=1)])


class UpdateTransactionCommentForm(Form):
    txn_id = id_field()
    comment = StringField(validators=[vals.Optional()])


class DeleteTransactionForm(Form):
    txn_id = id_field()


class AddExpenseLimitForm(Form):
    category_id = id_field()
    limit = StringField(validators=[vals.InputRequired()])


class DeleteExpenseLimitForm(Form):
    limit_id = id_field()


class ImportTransactionsForm(Form):
    provider_id = StringField(validators=[vals.Required()])
