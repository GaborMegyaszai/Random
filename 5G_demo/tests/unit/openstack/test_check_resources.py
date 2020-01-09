import unittest, json
from unittest.mock import patch, mock_open, MagicMock
from scripts.openstack import check_resources

class TestCheckResources(unittest.TestCase):

    def setUp(self):
        check_resources.connection = MagicMock()

    def test_get_flavors_from_nsd(self):
        read_data = json.dumps({
            "vnfd":[
                {
                    "name":"first",
                    "deployment_flavour":[
                        {
                            "flavour_key":"m1.large"
                        }
                    ]
                },
                {
                    "name":"second",
                    "deployment_flavour":[
                        {
                            "flavour_key":"m1.small"
                        }
                    ]
                }
            ]
        })
        with patch("builtins.open", mock_open(read_data=read_data)):
            result = check_resources.get_flavors_from_nsd("mock")
            self.assertEqual(result, ["m1.large", "m1.small"])

    def test_get_flavors_from_nsd_invalid_json_format(self):
        invalid_json = json.dumps({"vnfd": "invalid"})
        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with self.assertRaises(ValueError) as cm:
                check_resources.get_flavors_from_nsd("mock")
            self.assertEqual(str(cm.exception), "NSD json is invalid. Exception message: string indices must be integers")

    def test_get_flavors_from_nsd_invalid_json_missing_keys(self):
        invalid_json = json.dumps({"wrong_key": "fails"})
        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with self.assertRaises(ValueError) as cm:
                check_resources.get_flavors_from_nsd("mock")
            self.assertEqual(str(cm.exception), "NSD json is missing key: 'vnfd'")

    def test_add_requirement_without_swap(self):
        requirements = {"ram": 4096, "vcpus": 2, "disk": 20}
        check_resources.add_requirement(requirements, MockFlavorDetail())
        self.assertEqual(requirements, {"ram": 6144, "vcpus": 3, "disk": 60})

    def test_add_requirement_with_swap(self):
        requirements = {"ram": 2048, "vcpus": 1, "disk": 40}
        check_resources.add_requirement(requirements, MockFlavorDetail(swap=20))
        self.assertEqual(requirements, {"ram": 4096, "vcpus": 2, "disk": 100})

    def test_get_flavor_by_name(self):
        mock_flavor = MockFlavorDetail()
        check_resources.connection.compute.flavors = MagicMock(return_value = [mock_flavor])
        result = check_resources.get_flavor_by_name("m1.mock")
        self.assertEqual(result, mock_flavor)

    def test_get_flavor_by_name_does_not_exist(self):
        check_resources.connection.compute.flavors = MagicMock(return_value = [MockFlavorDetail()])
        with self.assertRaises(ValueError) as cm:
            check_resources.get_flavor_by_name("m1.nonexistent")
        self.assertEqual(str(cm.exception), "No flavor was found with name: m1.nonexistent")

    def test_check_hypervisor_resources_available_resources(self):
        hypervisor = {"id":1, "name":"mock-hypervisor", "memory_free":2048, "vcpus":16, "vcpus_used":14, "local_disk_free":20}
        check_resources.connection.compute.hypervisors = MagicMock(return_value = [hypervisor])
        requirements = {"ram": 2048, "vcpus": 2, "disk": 20}
        result = check_resources.check_hypervisor_resources(requirements)
        self.assertEqual(result, hypervisor)

    def test_check_hypervisor_resources_multiple_resources(self):
        insufficient = {"id":1, "name":"mock-insufficient", "memory_free":3000, "vcpus":6, "vcpus_used":5, "local_disk_free":60}
        sufficient = {"id":2, "name":"mock-sufficient", "memory_free":6000, "vcpus":16, "vcpus_used":12, "local_disk_free":60}
        check_resources.connection.compute.hypervisors = MagicMock(return_value = [insufficient, sufficient])
        requirements = {"ram": 2048, "vcpus": 2, "disk": 20}
        result = check_resources.check_hypervisor_resources(requirements)
        self.assertEqual(result, sufficient)

    def test_check_hypervisor_resources_no_available_resources(self):
        requirements = {"ram":2048, "vcpus":2, "disk":20}
        missing_ram = {"id":1, "name":"insufficient-ram", "memory_free":1024, "vcpus":8, "vcpus_used":2, "local_disk_free":40}
        missing_vcpus = {"id":2, "name":"insufficient-vcpus", "memory_free":6000, "vcpus":4, "vcpus_used":3, "local_disk_free":40}
        missing_disk = {"id":3, "name":"insufficient-disk", "memory_free":6000, "vcpus":8, "vcpus_used":2, "local_disk_free":15}
        # Return different hypervisor mock each time the method is called so all conditions get tested
        check_resources.connection.compute.hypervisors = MagicMock(side_effect=[[missing_ram], [missing_vcpus], [missing_disk]])
        for i in range(3):
            self.assertRaises(ValueError, check_resources.check_hypervisor_resources, requirements)

    def test_get_system_requirements_for_flavors(self):
        large_flavor = MockFlavorDetail("m1.large", 4096, 2, 40, None, 40)
        check_resources.get_flavor_by_name = MagicMock(side_effect=[MockFlavorDetail(), MockFlavorDetail(), large_flavor])
        result = check_resources.get_system_requirements_for_flavors(["m1.mock,", "m1.mock", "m1.large"])
        self.assertEqual(result, {"ram": 8192, "vcpus": 4, "disk": 160})


class MockFlavorDetail(object):
    def __init__(self, name="m1.mock", ram=2048, vcpus=1, disk=20, swap=None, ephemeral=20):
        self.name = name
        self.ram = ram
        self.vcpus = vcpus
        self.disk = disk
        self.swap = swap
        self.ephemeral = ephemeral


if __name__ == "__main__":
    unittest.main()
