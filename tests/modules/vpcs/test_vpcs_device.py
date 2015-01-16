# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
import asyncio
from tests.utils import asyncio_patch

#Move loop to util
from tests.api.base import loop, port_manager
from asyncio.subprocess import Process
from unittest.mock import patch, MagicMock
from gns3server.modules.vpcs.vpcs_device import VPCSDevice
from gns3server.modules.vpcs.vpcs_error import VPCSError

@patch("subprocess.check_output", return_value="Welcome to Virtual PC Simulator, version 0.6".encode("utf-8"))
def test_vm(tmpdir, port_manager):
    vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
    assert vm.name == "test"
    assert vm.id == 42

@patch("subprocess.check_output", return_value="Welcome to Virtual PC Simulator, version 0.1".encode("utf-8"))
def test_vm_invalid_vpcs_version(tmpdir, port_manager):
    with pytest.raises(VPCSError):
        vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
        assert vm.name == "test"
        assert vm.id == 42

@patch("gns3server.config.Config.get_section_config", return_value = {"path": "/bin/test_fake"})
def test_vm_invalid_vpcs_path(tmpdir, port_manager):
    with pytest.raises(VPCSError):
        vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
        assert vm.name == "test"
        assert vm.id == 42

def test_start(tmpdir, loop, port_manager):
    with asyncio_patch("asyncio.create_subprocess_exec", return_value=MagicMock()):
        vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
        nio = vm.port_add_nio_binding(0, {"type": "nio_udp", "lport": 4242, "rport": 4243, "rhost": "127.0.0.1"})

        loop.run_until_complete(asyncio.async(vm.start()))
        assert vm.is_running() == True

def test_stop(tmpdir, loop, port_manager):
    process = MagicMock()
    with asyncio_patch("asyncio.create_subprocess_exec", return_value=process):
        vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
        nio = vm.port_add_nio_binding(0, {"type": "nio_udp", "lport": 4242, "rport": 4243, "rhost": "127.0.0.1"})

        loop.run_until_complete(asyncio.async(vm.start()))
        assert vm.is_running() == True
        loop.run_until_complete(asyncio.async(vm.stop()))
        assert vm.is_running() == False
        process.terminate.assert_called_with()

def test_add_nio_binding_udp(port_manager, tmpdir):
    vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
    nio = vm.port_add_nio_binding(0, {"type": "nio_udp", "lport": 4242, "rport": 4243, "rhost": "127.0.0.1"})
    assert nio.lport == 4242

def test_add_nio_binding_tap(port_manager, tmpdir):
    vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
    with patch("gns3server.modules.vpcs.vpcs_device.has_privileged_access", return_value=True):
        nio = vm.port_add_nio_binding(0, {"type": "nio_tap", "tap_device": "test"})
        assert nio.tap_device == "test"

def test_add_nio_binding_tap_no_privileged_access(port_manager, tmpdir):
    vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
    with patch("gns3server.modules.vpcs.vpcs_device.has_privileged_access", return_value=False):
        with pytest.raises(VPCSError):
            vm.port_add_nio_binding(0, {"type": "nio_tap", "tap_device": "test"})
    assert vm._ethernet_adapter.ports[0] is not None

def test_port_remove_nio_binding(port_manager, tmpdir):
    vm = VPCSDevice("test", 42, port_manager, working_dir=str(tmpdir))
    nio = vm.port_add_nio_binding(0, {"type": "nio_udp", "lport": 4242, "rport": 4243, "rhost": "127.0.0.1"})
    vm.port_remove_nio_binding(0)
    assert vm._ethernet_adapter.ports[0] == None
