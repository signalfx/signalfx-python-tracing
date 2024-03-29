# Copyright (C) 2018-2019 SignalFx. All rights reserved.
from subprocess import check_output, CalledProcessError, STDOUT
import os.path
import os

from six import text_type as tt
import pytest

target = os.path.join(os.path.dirname(__file__), "lib/runner_target_script.py")
target_args = [
    "--one",
    "123",
    "--two",
    "123.456",
    "--three",
    "This Is A String",
    "-i",
    "1",
    "2",
    "3",
    "4",
    "5",
    "-j",
    "1",
    "2",
    "3",
    "4",
    "5",
    "-t",
    "collision1",
    "--token",
    "collision2",
    "--unknown=asdf",
    "-u" "file.py",
    "file.txt",
]


class TestRunner(object):
    @pytest.fixture(scope="class", autouse=True)
    def clear_token(self):
        token = os.environ.pop("SIGNALFX_ACCESS_TOKEN", None)
        yield
        if token:
            os.environ["SIGNALFX_ACCESS_TOKEN"] = token

    @pytest.fixture(scope="class", autouse=True)
    def clear_tracing_enabled_env_var(self):
        val = os.environ.pop("SIGNALFX_TRACING_ENABLED", None)
        yield
        if val:
            os.environ["SIGNALFX_TRACING_ENABLED"] = val

    @pytest.fixture
    def add_existing_sitecustomize(self):
        py_path = os.environ.get("PYTHONPATH", "")
        cwd = os.path.abspath(os.path.dirname(__file__))
        os.environ["PYTHONPATH"] = cwd + os.pathsep + py_path if py_path else cwd
        yield
        os.environ["PYTHONPATH"] = py_path

    def check_output(self, arg_ls, **kwargs):
        return check_output(arg_ls, stderr=STDOUT, **kwargs)

    def test_token_arg_optional_without_env_var(self):
        with pytest.raises(Exception) as e:
            self.check_output(["sfx-py-trace", "file.py"])
        # check that target run attempted after instrumentation
        expected = "can't open file 'file.py': [Errno 2] No such file or directory"
        assert expected in tt(e.value.output)

    def test_env_var_missing_target(self):
        env = dict(os.environ)
        env["SIGNALFX_ACCESS_TOKEN"] = "123"
        with pytest.raises(CalledProcessError) as e:
            self.check_output(["sfx-py-trace"], env=env)
        output = tt(e.value.output)
        assert (
            "too few arguments" in output
            or "the following arguments are required: target" in output
        )

    def test_flag_missing_target(self):
        with pytest.raises(CalledProcessError) as e:
            self.check_output(["sfx-py-trace", "-t", "123"])
        output = tt(e.value.output)
        assert (
            "too few arguments" in output
            or "the following arguments are required: target" in output
        )

    def test_named_missing_target(self):
        with pytest.raises(CalledProcessError) as e:
            self.check_output(["sfx-py-trace", "--token", "123"])
        output = tt(e.value.output)
        assert (
            "too few arguments" in output
            or "the following arguments are required: target" in output
        )

    def test_flag_missing_target_args(self):
        with pytest.raises(CalledProcessError) as e:
            self.check_output(["sfx-py-trace", "-t", "123", target])
        output = tt(e.value.output)
        assert "required" in output or "--one" in output

    def test_flag_with_target_args(self):
        self.check_output(["sfx-py-trace", "-t", "123", target] + target_args)

    def test_named_missing_target_args(self):
        with pytest.raises(CalledProcessError) as e:
            self.check_output(["sfx-py-trace", "--token", "123", target])
        output = tt(e.value.output)
        assert "required" in output or "--one" in output

    def test_named_with_token_and_target_args(self):
        self.check_output(["sfx-py-trace", "--token", "123", target] + target_args)

    def test_named_with_token_env_var_and_target_args(self):
        env = dict(os.environ)
        env["SIGNALFX_ACCESS_TOKEN"] = "123"
        self.check_output(["sfx-py-trace", target] + target_args, env=env)

    def test_named_without_token_and_target_args(self):
        self.check_output(["sfx-py-trace", target] + target_args)

    def test_disabled_env_var_prevents_site_addition(self):
        os.environ["SIGNALFX_TRACING_ENABLED"] = "False"
        with pytest.raises(CalledProcessError) as e:
            self.check_output(["sfx-py-trace", target] + target_args)
        output = tt(e.value.output)
        assert "assert isinstance(opentracing.tracer, Tracer)" in output

    def test_enabled_env_var_doesnt_prevents_site_addition(self):
        os.environ["SIGNALFX_TRACING_ENABLED"] = "True"
        self.check_output(["sfx-py-trace", target] + target_args)

    def test_existing_sitecustomize_called(self, add_existing_sitecustomize):
        assert not len(
            self.check_output(
                ["sfx-py-trace", target] + target_args + ["--sitecustomize"]
            )
        )

    def test_no_existing_sitecustomize_doesnt_cause_noise(self):
        assert not len(self.check_output(["sfx-py-trace", target] + target_args))
