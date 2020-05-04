"""
Run with:

python -m unittest tests.test
"""
from unittest import TestCase
from graphene_chain_mutation import ShareResultMiddleware
from .fake import schema


class ShareResultTestCase(TestCase):

    def test_1_chained_creation_works(self):
        result = self._execute_chained_creations()
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
        #
        self._assert_emilie(result.data.get("emilie", {}))
        self._assert_john(result.data.get("john", {}))
        self._assert_julie(result.data.get("julie", {}))
        #
        self.assertEqual(result.data.get("e1", {}).get("ok"), True)
        self.assertEqual(result.data.get("e2", {}).get("ok"), True)
        self.assertEqual(result.data.get("e3", {}).get("ok"), True)
        ###
        result = self._execute_query()
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
        #
        parents = result.data.get("parents")
        self.assertIsNotNone(parents)
        self.assertEqual(len(parents), 1)
        self._assert_emilie(parents[0])
        #
        children = result.data.get("children")
        self.assertIsNotNone(children)
        self.assertEqual(len(children), 2)
        self._assert_john(children[0])
        self._assert_julie(children[1])
        #
        self._assert_emilie(children[0].get("parent"))
        self._assert_emilie(children[1].get("parent"))
        #
        self._assert_julie(children[0]["siblings"][0])
        self._assert_john(children[1]["siblings"][0])

    def test_2_chained_update_and_creation_works(self):
        result = self._execute_chained_updates_and_creations()
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
        #
        self._assert_emilie(result.data.get("emilie", {}))
        self._assert_robert(result.data.get("robert", {}))
        self._assert_john(result.data.get("john", {}))
        self._assert_lucie(result.data.get("lucie", {}))
        #
        self.assertEqual(result.data.get("e1", {}).get("ok"), True)
        self.assertEqual(result.data.get("e2", {}).get("ok"), True)
        ###
        result = self._execute_query()
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
        #
        parents = result.data.get("parents")
        self.assertIsNotNone(parents)
        self.assertEqual(len(parents), 2)
        self._assert_emilie(parents[0])
        self._assert_robert(parents[1])
        #
        children = result.data.get("children")
        self.assertIsNotNone(children)
        self.assertEqual(len(children), 3)
        self._assert_john(children[0])
        self._assert_julie(children[1])
        self._assert_lucie(children[2])
        #
        self._assert_robert(children[0].get("parent"))
        self._assert_emilie(children[1].get("parent"))
        self._assert_emilie(children[2].get("parent"))
        #
        self._assert_julie(children[0]["siblings"][0])
        self._assert_lucie(children[0]["siblings"][1])
        self._assert_john(children[1]["siblings"][0])

    def test_3_share_result_middleware_does_not_mess_normal_mutations(self):
        result = self._execute_normal_mutation()
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
        #
        self._assert_alex(result.data.get("alex", {}))

    def test_4_nested_mutation_can_ref_root_mutation(self):
        result = self._execute_nested_mutation_ref_root()
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
        #
        self._assert_tessa(result.data.get("tessa", {}))
        self._assert_bill(result.data.get("bill", {}))
        self._assert_cassandre(result.data.get("cassandre", {}))
        ###
        result = self._execute_query()
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data)
        #
        parents = result.data.get("parents")
        self.assertIsNotNone(parents)
        self.assertEqual(len(parents), 4)
        self._assert_emilie(parents[0])
        self._assert_robert(parents[1])
        self._assert_alex(parents[2])
        self._assert_tessa(parents[3])
        #
        children = result.data.get("children")
        self.assertIsNotNone(children)
        self.assertEqual(len(children), 5)
        self._assert_john(children[0])
        self._assert_julie(children[1])
        self._assert_lucie(children[2])
        self._assert_bill(children[3])
        self._assert_cassandre(children[4])
        #
        self._assert_robert(children[0].get("parent"))
        self._assert_emilie(children[1].get("parent"))
        self._assert_emilie(children[2].get("parent"))
        self._assert_tessa(children[3].get("parent"))
        self._assert_tessa(children[4].get("parent"))

    @staticmethod
    def _execute_query():
        query = """
            query {
                parents {
                    pk
                    name
                }

                children {
                    pk
                    name
                    parent { pk name }
                    siblings { pk name }
                }
            }
        """
        return schema.execute(
            query
            , middleware=[ShareResultMiddleware()]
        )

    @staticmethod
    def _execute_chained_creations():
        query = """
            mutation ($emilie: ParentInput, $john: ChildInput, $julie: ChildInput) {
                emilie: upsertParent(data: $emilie) {
                    pk
                    name
                }

                john: upsertChild(data: $john) {
                    pk
                    name
                }

                julie: upsertChild(data: $julie) {
                    pk
                    name
                }

                e1: setParent(parent: "emilie", child: "john") { ok }

                e2: setParent(parent: "emilie", child: "julie") { ok }

                e3: addSibling(node1: "john", node2: "julie") { ok }
            }
        """
        return schema.execute(
            query
            , variables=dict(
                emilie=dict(
                    name="Emilie"
                )
                , john=dict(
                    name="John"
                )
                , julie=dict(
                    name="Julie"
                )
            )
            , middleware=[ShareResultMiddleware()]
        )

    @staticmethod
    def _execute_chained_updates_and_creations():
        query = """
            mutation ($emilie: ParentInput, $robert: ParentInput, $john: ChildInput, $lucie: ChildInput) {
                emilie: upsertParent(data: $emilie) {
                    pk
                    name
                }

                robert: upsertParent(data: $robert) {
                    pk
                    name
                }

                john: upsertChild(data: $john) {
                    pk
                    name
                }

                lucie: upsertChild(data: $lucie) {
                    pk
                    name
                }

                e1: setParent(parent: "robert", child: "john") { ok }

                e2: addSibling(node1: "lucie", node2: "john") { ok }

                # we don't need the above, we know the PK of emilie
                # e3: setParent(parent: "emilie", child: "lucie") { ok }
            }
        """
        return schema.execute(
            query
            , variables=dict(
                emilie=dict(
                    pk=1
                    ,name="Emilie"
                )
                ,robert=dict(
                    name="Robert"
                )
                ,john=dict(
                    pk=1
                    ,name="John"
                    ,parent=None
                    ,siblings=[2]
                )
                ,lucie=dict(
                    name="Lucie"
                    ,parent=1
                )
            )
            , middleware=[ShareResultMiddleware()]
        )

    @staticmethod
    def _execute_normal_mutation():
        query = """
        mutation ($alex: ParentInput) {
            alex: normalParentMutation (data: $alex) {
                pk
                name
            }
        }
        """
        return schema.execute(
            query
            ,variables=dict(
                alex=dict(
                    name="Alex"
                )
            )
            ,middleware=[ShareResultMiddleware()]
        )

    @staticmethod
    def _execute_nested_mutation_ref_root():
        query = """
        mutation ($tessa: ParentInput, $bill: ChildInput, $cassandre: ChildInput) {
            tessa: upsertParent(data: $tessa) {
                pk
                name
            }
            
            bill: createChild(data: $bill) {
                pk
                name
                parent: refParent(ref: "tessa") {
                  pk
                  name
                }
            }
            
            cassandre: createChild(data: $cassandre) {
                pk
                name
                parent: refParent(ref: "tessa") {
                  pk
                  name
                }
            }
        }
        """
        return schema.execute(
            query
            , variables=dict(
                tessa=dict(
                    name="Tessa"
                )
                , bill=dict(
                    name="Bill"
                )
                , cassandre=dict(
                    name="Cassandre"
                )
            )
            , middleware=[ShareResultMiddleware()]
        )

    def _assert_emilie(self, emilie: dict):
        self.assertIsNotNone(emilie)
        self.assertEqual(emilie.get("pk"), 1)
        self.assertEqual(emilie.get("name"), "Emilie")

    def _assert_robert(self, robert: dict):
        self.assertIsNotNone(robert)
        self.assertEqual(robert.get("pk"), 2)
        self.assertEqual(robert.get("name"), "Robert")

    def _assert_alex(self, alex: dict):
        self.assertIsNotNone(alex)
        self.assertEqual(alex.get("pk"), 3)
        self.assertEqual(alex.get("name"), "Alex")

    def _assert_tessa(self, tessa: dict):
        self.assertIsNotNone(tessa)
        self.assertEqual(tessa.get("pk"), 4)
        self.assertEqual(tessa.get("name"), "Tessa")

    def _assert_john(self, john: dict):
        self.assertIsNotNone(john)
        self.assertEqual(john.get("pk"), 1)
        self.assertEqual(john.get("name"), "John")

    def _assert_julie(self, julie: dict):
        self.assertIsNotNone(julie)
        self.assertEqual(julie.get("pk"), 2)
        self.assertEqual(julie.get("name"), "Julie")

    def _assert_lucie(self, lucie: dict):
        self.assertIsNotNone(lucie)
        self.assertEqual(lucie.get("pk"), 3)
        self.assertEqual(lucie.get("name"), "Lucie")

    def _assert_bill(self, bill: dict):
        self.assertIsNotNone(bill)
        self.assertEqual(bill.get("pk"), 4)
        self.assertEqual(bill.get("name"), "Bill")

    def _assert_cassandre(self, cassandre: dict):
        self.assertIsNotNone(cassandre)
        self.assertEqual(cassandre.get("pk"), 5)
        self.assertEqual(cassandre.get("name"), "Cassandre")