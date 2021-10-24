from wtforms import DateTimeField
from wtforms import Form
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import validators as vals

from myfunds.web import constants


username_field = lambda: StringField(  # noqa: E731
    validators=[vals.InputRequired(), vals.Regexp(r"^[a-zA-Z0-9_]{4,100}$")]
)
password_field = lambda: PasswordField(  # noqa: E731
    validators=[vals.InputRequired(), vals.Length(min=6, max=100)]
)
id_field = lambda: IntegerField(  # noqa: E731
    validators=[vals.InputRequired(), vals.NumberRange(min=1)]
)


class LoginForm(Form):
    username = username_field()
    password = password_field()


class AddAccountForm(Form):
    username = username_field()
    password = password_field()
    password_copy = PasswordField(
        validators=[vals.InputRequired(), vals.EqualTo("password")]
    )


class UpdateAccountPasswordForm(Form):
    account_id = id_field()
    old_password = password_field()
    new_password = password_field()
    new_password_copy = PasswordField(
        validators=[vals.InputRequired(), vals.EqualTo("new_password")]
    )


class DeleteAccountForm(Form):
    account_id = id_field()
    passphrase = StringField(
        validators=[vals.InputRequired(), vals.Regexp(r"delete this account")]
    )


class AddCurrencyForm(Form):
    code_alpha = StringField(
        validators=[vals.InputRequired(), vals.Regexp(r"^[a-zA-Z]{3}$")]
    )
    precision = IntegerField(validators=[vals.InputRequired(), vals.NumberRange(min=0)])


class DeleteCurrencyForm(Form):
    currency_id = id_field()


class AddCategoryForm(Form):
    direction = StringField(
        validators=[vals.InputRequired(), vals.AnyOf(constants.FundsDirection.values())]
    )
    name = StringField(validators=[vals.InputRequired()])
    color_sign = StringField(
        validators=[vals.InputRequired(), vals.Regexp(r"^#[a-f0-9]{6}$")]
    )


class EditCategoryForm(Form):
    category_id = id_field()
    name = StringField(validators=[vals.Optional()])
    color_sign = StringField(
        validators=[vals.Optional(), vals.Regexp(r"^#[a-f0-9]{6}$")]
    )


class DeleteCategoryForm(Form):
    category_id = id_field()


class AddBalanceForm(Form):
    name = StringField(validators=[vals.InputRequired()])
    currency = StringField(
        validators=[vals.InputRequired(), vals.Regexp(r"^[A-Z]{3}$")]
    )


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


class AddBalanceLimitForm(Form):
    category_id = id_field()
    amount = StringField(validators=[vals.InputRequired()])


class DeleteBalanceLimitForm(Form):
    limit_id = id_field()


class ImportTransactionsForm(Form):
    parser_id = StringField(validators=[vals.InputRequired()])


class AddJointLimitForm(Form):
    currency_id = id_field()
    name = StringField(validators=[vals.InputRequired()])
    amount = IntegerField(validators=[vals.InputRequired(), vals.NumberRange(min=1)])


class DeleteJointLimitForm(Form):
    limit_id = id_field()


class JointLimitParticipantGetStepForm(Form):
    step = IntegerField(validators=[vals.InputRequired(), vals.AnyOf([1, 2])])


class AddJointLimitParticipantStep1Form(Form):
    account_id = id_field()


class AddJointLimitParticipantStep2Form(Form):
    account_id = id_field()
    category_id = id_field()


class DeleteJointLimitParticipantForm(Form):
    participant_id = id_field()


class AddCryptoCurrencyForm(Form):
    url = StringField(validators=[vals.InputRequired(), vals.URL()])


class DeleteCryptoCurrencyForm(Form):
    currency_id = id_field()


class AddCryptoBalanceForm(Form):
    name = StringField(validators=[vals.InputRequired()])
    currency_id = id_field()


class DeleteCryptoBalanceForm(Form):
    balance_id = id_field()


class UpdateCryptoBalanceQuantityForm(Form):
    balance_id = id_field()
    action = StringField(
        validators=[vals.InputRequired(), vals.AnyOf(["set", "add", "subtract"])]
    )
    quantity = StringField(validators=[vals.InputRequired()])


class AddCyptoTransactionForm(Form):
    currency_id = id_field()
    quantity = StringField(validators=[vals.InputRequired()])
    price = StringField(validators=[vals.InputRequired()])
