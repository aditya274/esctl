import esctl.cmd.cluster
from base_test_class import EsctlTestCase


class TestClusterHealth(EsctlTestCase):
    def setUp(self):
        super()._setUp()
        self.mock("cluster.health")
        self.cluster_health = esctl.cmd.cluster.ClusterHealth(self.app, {})

    def fixture(self):
        return {
            "cluster_name": "test",
            "status": "green",
            "timed_out": "false",
            "number_of_nodes": 92,
            "number_of_data_nodes": 87,
            "active_primary_shards": 765,
            "active_shards": 2295,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 0,
            "delayed_unassigned_shards": 0,
            "number_of_pending_tasks": 0,
            "number_of_in_flight_fetch": 0,
            "task_max_waiting_in_queue_millis": 0,
            "active_shards_percent_as_number": 100.0,
        }

    def test_health_status_color(self):
        self.assertEqual(
            self.cluster_health.colorize_cluster_status("green")[0], "\x1b[92m"
        )
        self.assertEqual(
            self.cluster_health.colorize_cluster_status("yellow")[0],
            "\x1b[93m",
        )
        self.assertEqual(
            self.cluster_health.colorize_cluster_status("red")[0], "\x1b[91m"
        )
