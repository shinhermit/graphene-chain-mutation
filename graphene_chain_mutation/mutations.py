"""
This package provide features to implement the idea of chaining GraphQL mutations
based on a Graph node+edge creation pattern, inspired by what is done with
Graphviz Dot for example.

The principle is to use a Graphene middleware (ShareResultMiddleware)
to inject a result holder in the resolvers and then use these results
to allow referencing a mutation result in another mutation of
the same query.
"""
from typing import List, Dict, Tuple, Type, Union
import graphene
from graphene import ObjectType, Int


Integers = Union[Int, int]  # fix type checks warnings


class ShareResultMiddleware:
    """
    Inject a "shared_results" dict as a kwarg in the resolvers to allow them
    expose their results to following resolvers.
    """

    shared_results = {}

    def resolve(self, next_resolver, root, info, **kwargs):
        if hasattr(next_resolver.args[0], "__self__") and \
                issubclass(next_resolver.args[0].__self__, SharedResultMutation):
            return next_resolver(root, info, shared_results=self.shared_results, **kwargs)
        else:
            return next_resolver(root, info, **kwargs)


class SharedResultMutation(graphene.Mutation):
    """
    A node-like mutation base that take into account the shared_results dict
    injected by the ShareResultMiddleware. The mutation will automatically expose
    its insert its results into the shared_results dict. Subclass must override
    the mutate_and_share_result method instead of mutate.
    
    Do not forget to use the ShareResultMiddleware when executing queries.
    """

    @classmethod
    def mutate(cls, root: None, info: graphene.ResolveInfo,
               shared_results: Dict[str, ObjectType], **kwargs):
        result = cls.mutate_and_share_result(root, info, **kwargs)
        assert root is None, "SharedResultMutation must be a root mutation." \
                             " Current mutation has a %s parent" % type(root)
        node = info.path[0]
        shared_results[node] = result
        return result

    @staticmethod
    def mutate_and_share_result(root: None, info: graphene.ResolveInfo, **kwargs):
        raise NotImplementedError("This method must be implemented in subclasses.")


class EdgeMutationBase(SharedResultMutation):
    """
    Edge-like mutation base. Just define the declares the common
    attribute "ok" and the abstract method mutate_and_share_result.
    """

    ok = graphene.Boolean()

    @classmethod
    def set_link(cls, node1: ObjectType, node2: ObjectType):
        raise NotImplementedError("This method must be implemented in subclasses.")

    @staticmethod
    def mutate_and_share_result(root: None, info: graphene.ResolveInfo, **__):
        raise AttributeError("This method is not used in edge mutations.")


def assert_input_node_types(shared_results: dict, node1: str, node2: str,
                            node1_type: Type[ObjectType],
                            node2_type: Type[ObjectType]) -> Tuple[ObjectType, ObjectType]:
    """
    Make assertions on the types of edge-like mutation inputs and return the
    corresponding "nodes" from the shared_results dict (See ShareResultMiddleware,
    SharedResultMutation and EdgeMutationBase)
    """
    node1_ = shared_results.get(node1)
    node2_ = shared_results.get(node2)
    assert node1_ is not None, "Node 1 not found in mutation results."
    assert node2_ is not None, "Node 2 not found in mutation results."
    assert node1_type is not None, "A type must be specified for Node 1."
    assert node2_type is not None, "A type must be specified for Node 2."
    assert isinstance(node1_, node1_type), "%s is not instance of %s" % \
                                           (type(node1_), node1_type.__name__)
    assert isinstance(node2_, node2_type), "%s is not instance of %s" % \
                                           (type(node2_), node2_type.__name__)
    return node1_, node2_


class ParentChildEdgeMutation(EdgeMutationBase):
    """
    Edge-like mutation for FK links. Subclasses only need to override the
    set_link method.
    """

    parent_type: Type[ObjectType] = None
    child_type: Type[ObjectType] = None

    class Arguments:
        parent = graphene.String(required=True)
        child = graphene.String(required=True)

    @classmethod
    def mutate(cls, root: None, info: graphene.ResolveInfo,
               shared_results: dict, parent: str="", child: str="", **__):
        parent_, child_ = assert_input_node_types(
            shared_results,
            node1=parent,
            node2=child,
            node1_type=cls.parent_type,
            node2_type=cls.child_type
        )
        cls.set_link(parent_, child_)
        cls.set_link(parent_, child_)
        return cls(ok=True)

    @classmethod
    def set_link(cls, node1: ObjectType, node2: ObjectType):
        raise NotImplementedError("This method must be implemented in subclasses.")


class SiblingEdgeMutation(EdgeMutationBase):
    """
    Edge-like mutation for m2m links. Subclasses only need to override the
    set_link method.
    """

    node1_type: Type[ObjectType] = None
    node2_type: Type[ObjectType] = None

    class Arguments:
        node1 = graphene.String(required=True)
        node2 = graphene.String(required=True)

    @classmethod
    def mutate(cls, root: None, info: graphene.ResolveInfo,
               shared_results: dict, node1: str="", node2: str="", **__):
        node1_, node2_ = assert_input_node_types(
            shared_results,
            node1=node1,
            node2=node2,
            node1_type=cls.node1_type,
            node2_type=cls.node2_type
        )
        cls.set_link(node1_, node2_)
        return cls(ok=True)

    @classmethod
    def set_link(cls, node1: ObjectType, node2: ObjectType):
        raise NotImplementedError("This method must be implemented in subclasses.")
