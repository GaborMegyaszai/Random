from robot.libraries.BuiltIn import BuiltIn

class DependencyLibrary(object):
    ROBOT_LISTENER_API_VERSION = 3
    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self):
        self.ROBOT_LIBRARY_LISTENER = self
        self.suite_statuses = {}

    def _end_suite(self, data, results):
        self.suite_statuses[data.name] = results.status

    def suite_should_have_passed(self, name):
        try:
            if self.suite_statuses[name] == "FAIL":
                raise Exception("Suite '" + name + "' failed")
        except KeyError:
            raise Exception("No suite with name '" + name + "' in finished suites: " + str(list(self.suite_statuses.keys()))) from None
