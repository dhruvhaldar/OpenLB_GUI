"""
Tests for Docker-based build integration.
Verifies that get_docker_cmd generates correct Docker commands,
including Windows-to-POSIX path translation and OLB_ROOT override.
"""
from backend.main import get_docker_cmd, DOCKER_IMAGE, DOCKER_OLB_ROOT, CONTAINER_WORKSPACE


def test_get_docker_cmd_simple_path():
    """Verifies Docker command generation for a simple case path."""
    cmd = get_docker_cmd(["make"], "cyl_flow")
    assert cmd[0:3] == ["docker", "run", "--rm"]
    assert "-v" in cmd
    assert DOCKER_IMAGE in cmd
    assert "make" in cmd
    assert f"OLB_ROOT={DOCKER_OLB_ROOT}" in cmd
    # Working directory should use POSIX path
    w_idx = cmd.index("-w")
    assert cmd[w_idx + 1] == f"{CONTAINER_WORKSPACE}/cyl_flow"


def test_get_docker_cmd_nested_path():
    """Verifies Docker command generation for a nested case path (domain/case)."""
    cmd = get_docker_cmd(["make"], "Benchmarks/lid_driven_cavity")
    w_idx = cmd.index("-w")
    assert cmd[w_idx + 1] == f"{CONTAINER_WORKSPACE}/Benchmarks/lid_driven_cavity"


def test_get_docker_cmd_windows_backslash():
    """Verifies that Windows backslashes are converted to POSIX forward slashes."""
    cmd = get_docker_cmd(["make"], "Benchmarks\\lid_driven_cavity")
    w_idx = cmd.index("-w")
    assert "\\" not in cmd[w_idx + 1]
    assert cmd[w_idx + 1] == f"{CONTAINER_WORKSPACE}/Benchmarks/lid_driven_cavity"


def test_get_docker_cmd_make_run():
    """Verifies Docker command includes 'make run' arguments."""
    cmd = get_docker_cmd(["make", "run"], "cyl_flow")
    # Both 'make' and 'run' should appear after the image name
    image_idx = cmd.index(DOCKER_IMAGE)
    args_after_image = cmd[image_idx + 1:]
    assert "make" in args_after_image
    assert "run" in args_after_image


def test_get_docker_cmd_olb_root_override():
    """Verifies OLB_ROOT is passed as the last argument to override Makefile values."""
    cmd = get_docker_cmd(["make"], "cyl_flow")
    assert cmd[-1] == f"OLB_ROOT={DOCKER_OLB_ROOT}"


def test_get_docker_cmd_bind_mount():
    """Verifies the bind mount flag is correctly structured."""
    cmd = get_docker_cmd(["make"], "cyl_flow")
    v_idx = cmd.index("-v")
    mount = cmd[v_idx + 1]
    # Should be in format HOST_PATH:CONTAINER_PATH
    assert ":" in mount
    assert mount.endswith(CONTAINER_WORKSPACE)
