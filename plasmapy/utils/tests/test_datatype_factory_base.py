import pytest

from plasmapy.utils.datatype_factory_base import (
    BasicRegistrationFactory,
    MultipleMatchError,
    NoMatchError,
    ValidationFunctionError,
)

# SunPy is released under a BSD-style open source license:

# Copyright (c) 2013-2018 The SunPy developers
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Project     : https://github.com/sunpy/sunpy
# File        : sunpy/util/tests/test_datatype_factory_base.py
# Commit hash : f6330eea602ea796b5b004dee283b8877b24da23


class BaseWidget:
    def __init__(self, *args, **kwargs):
        pass


class DefaultWidget(BaseWidget):
    pass


class StandardWidget(BaseWidget):
    @classmethod
    def _factory_validation_function(cls, *args, **kwargs):
        return kwargs.get("style") == "standard"


class DuplicateStandardWidget(BaseWidget):
    @classmethod
    def _factory_validation_function(cls, *args, **kwargs):
        return kwargs.get("style") == "standard"


class FancyWidget(BaseWidget):
    @classmethod
    def _factory_validation_function(cls, *args, **kwargs):
        return kwargs.get("style") == "fancy" and "feature" in kwargs


class ExternallyValidatedWidget(BaseWidget):
    pass


def external_validation_function(*args, **kwargs):
    return kwargs.get("style") == "external"


class UnvalidatedWidget(BaseWidget):
    pass


class MissingClassMethodWidget(BaseWidget):
    def _factory_validation_function(cls, *args, **kwargs):
        return kwargs.get("style") == "missing"


class DifferentValidationWidget(BaseWidget):
    @classmethod
    def different_validation_function(cls, *args, **kwargs):
        return kwargs.get("style") == "different"


class MissingClassMethodDifferentValidationWidget(BaseWidget):
    def different_validation_function(cls, *args, **kwargs):
        return kwargs.get("style") == "missing-different"


class TestBasicRegistrationFactory:
    def test_default_factory(self):
        DefaultFactory = BasicRegistrationFactory()

        DefaultFactory.register(DefaultWidget, is_default=True)
        assert DefaultFactory.default_widget_type == DefaultWidget

        DefaultFactory.register(StandardWidget)
        DefaultFactory.register(FancyWidget)
        DefaultFactory.register(
            ExternallyValidatedWidget, validation_function=external_validation_function
        )

        assert type(DefaultFactory()) is DefaultWidget
        assert type(DefaultFactory(style="standard")) is StandardWidget
        assert type(DefaultFactory(style="fancy")) is DefaultWidget
        assert type(DefaultFactory(style="fancy", feature="present")) is FancyWidget
        assert type(DefaultFactory(style="external")) is ExternallyValidatedWidget

        with pytest.raises(ValidationFunctionError):
            DefaultFactory.register(UnvalidatedWidget)

        with pytest.raises(ValidationFunctionError):
            DefaultFactory.register(MissingClassMethodWidget)

        DefaultFactory.unregister(StandardWidget)
        assert type(DefaultFactory(style="standard")) is not StandardWidget

    def test_validation_fun_not_callable(self):
        TestFactory = BasicRegistrationFactory()

        with pytest.raises(AttributeError):
            TestFactory.register(StandardWidget, validation_function="not_callable")

    def test_no_default_factory(self):
        NoDefaultFactory = BasicRegistrationFactory()

        NoDefaultFactory.register(StandardWidget)
        NoDefaultFactory.register(FancyWidget)

        with pytest.raises(NoMatchError):
            NoDefaultFactory()

        # Raises because all requirements are not met for FancyWidget and no
        # default is present.
        with pytest.raises(NoMatchError):
            NoDefaultFactory(style="fancy")

        assert type(NoDefaultFactory(style="standard")) is StandardWidget
        assert type(NoDefaultFactory(style="fancy", feature="present")) is FancyWidget

    def test_with_external_registry(self):
        external_registry = {}

        FactoryWithExternalRegistry = BasicRegistrationFactory(
            registry=external_registry
        )

        assert len(external_registry) == 0

        FactoryWithExternalRegistry.register(StandardWidget)
        assert type(FactoryWithExternalRegistry(style="standard")) is StandardWidget

        # Ensure the 'external_registry' is being populated see #1988
        assert len(external_registry) == 1

    def test_multiple_match_factory(self):
        MultipleMatchFactory = BasicRegistrationFactory()

        MultipleMatchFactory.register(StandardWidget)
        MultipleMatchFactory.register(DuplicateStandardWidget)

        with pytest.raises(MultipleMatchError):
            MultipleMatchFactory(style="standard")

    def test_extra_validation_factory(self):
        ExtraValidationFactory = BasicRegistrationFactory(
            additional_validation_functions=["different_validation_function"]
        )

        ExtraValidationFactory.register(DifferentValidationWidget)

        assert (
            type(ExtraValidationFactory(style="different")) is DifferentValidationWidget
        )

        with pytest.raises(ValidationFunctionError):
            ExtraValidationFactory.register(MissingClassMethodDifferentValidationWidget)
