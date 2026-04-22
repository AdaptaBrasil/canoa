
"""
Equipe da Canoa -- 2024

WTForms utilities

mgd 2024-06-22

"""

# cSpell:ignore wtforms


class LenValidate:
    """
    A class that validates a value within a specified minimum and maximum length.

    Args:
        min (int): The minimum allowed length.
        max (int): The maximum allowed length (optional, defaults to None).

    Raises:
        ValueError: If `min` is not a positive integer or if `max` is less than `min`.
    """

    def __init__(self, min: int, max: int | None = None) -> None:
        if not isinstance(min, int) or min <= 0:
            raise ValueError("`min` must be a positive integer.")
        if max is not None and max < min:
            raise ValueError("`max` cannot be less than `min`.")

        self.min = min
        self.max = max

    def check(self, value: str) -> bool:
        """
        Checks if the provided value meets the length requirements.

        Args:
            value (str): The value to be validated.

        Returns:
            bool: True if the value is valid, False otherwise.
        """

        if not isinstance(value, str):
            raise TypeError("`value` must be a string.")

        length = len(value)
        return self.min <= length <= self.max if self.max is not None else length >= self.min

    def wtf_val(self) -> dict:
        """
        Returns:
            dict: A dictionary containing the wtforms Length validator arguments.

                Note that it is sent to the HTML input `max + 1` because the input
                tag does not allow you to write more digits than the maximum and,
                if your password is close to max (+1 +2), you may not notice the
                fact that did not write all your password, believing that you have
                actually written the n characters of your password.
                This way, the server side has to check and send a message.
                (This is due to my own experience (mgd))
        """
        return {"min": self.min, "max": -1 if self.max is None else self.max + 1}


# # Example usage
# validator = LenValidate(8, 20)  # Minimum length of 8, maximum of 20

# if not validator.check("This is a valid string"):
#     print("Invalid length")

# # Using the wtforms validator
# from wtforms import Form, StringField

# class MyForm(Form):
#     password = StringField('Password', validators=[Length( **len_validate.wtf_val() ) ])


#####
""" from wtforms import Label, StringField, PasswordField, Form

class CustomLabel(Label):
    def __init__(self, text="", **kwargs):
        super().__init__(text)
        self.attributes = kwargs

    def __call__(self):
        # Build the label HTML with dynamic attributes
        attrs = " ".join(f'{key}="{value}"' for key, value in self.attributes.items())
        return f'<label {attrs}>{self.text}</label>'

class MyForm(Form):
    password_label = CustomLabel("Confirm Password", for="pwdConfirm", class="custom-label")
    password = PasswordField("", render_kw={"class": "form-control", "id": "pwdConfirm"})


from wtforms import PasswordField, Form

class DynamicLabelField(PasswordField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render_label(self, text="", **kwargs):
        # Generate dynamic attributes
        attrs = " ".join(f'{key}="{value}"' for key, value in kwargs.items())
        return f'<label {attrs}>{text}</label>'

class MyForm(Form):
    password = DynamicLabelField("", render_kw={"class": "form-control", "id": "pwdConfirm"})



{{ form.password.render_label(text=labelText, for="pwdConfirm", class="custom-label") }}
{{ form.password }}

"""

# eof
