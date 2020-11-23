"""
This package provide features to implement the idea of chaining GraphQL mutations
based on a Graph node+edge creation pattern, inspired by what is done with
Graphviz Dot for example.

The principle is to use a Graphene middleware (ShareResultMiddleware)
to inject a result holder in the resolvers and then use these results
to allow referencing a mutation result in another mutation of
the same query.
"""
from typing import Tuple, Type, Union
import graphene
from graphene import ObjectType, Int


Integers = Union[Int, int]  # fix type checks warnings


class ShareResultMiddleware:
    """
    Inject a "shared_results" dict in the context to allow resolvers to
    expose their results to following resolvers.

    This middleware allow to systematically share the results of all resolver.
    For a more selective sharing, use the ShareResult class.
    """
    def resolve(self, next_resolver, root, info: graphene.ResolveInfo, **kwargs):
        assert info.context is not None, "Please provide an execution context. "\
                                         "A simple class like `class NullContext: pass` "\
                                         "would do the trick."
        if not hasattr(info.context, "shared_results"):
            info.context.shared_results = {}
        result =  next_resolver(root, info, **kwargs)
        node = info.path[0]
        info.context.shared_results[node] = result
        return result


class ShareResult:
    """
    A node-like mutation base that take into account the shared_results dict
    injected by the ShareResultMiddleware. The mutation will automatically
    insert its results into the shared_results dict.

    Do not forget to use the ShareResultMiddleware with your schema
    when executing queries.
    """

    @classmethod
    def __init_subclass__(cls, **options):
        """
        We have to use __init_subclass__ because graphene does. We need to
        transform the "mutate" method before graphene.Mutation's method __init_subclass__
        uses it to create a resolver.
        """
        initial_mutate = cls.mutate
        def mutate(root: None, info: graphene.ResolveInfo, **kwargs):
            assert root is None, "SharedResult mutation must be a root mutation." \
                                 " Current mutation has a %s parent" % type(root)
            assert info.context is not None, "Please provide an execution context. "\
                                             "A simple class like `class NullContext: pass` "\
                                             "would do the trick."
            if not hasattr(info.context, "shared_results"):
                info.context.shared_results = {}
            result = initial_mutate(root, info, **kwargs)
            node = info.path[0]
            info.context.shared_results[node] = result
            return result
        cls.mutate = mutate
        super().__init_subclass__(**options)


class EdgeMutationBase:
    """
    Edge-like mutation base.

    Just the declares the common attribute "ok" and
    the abstract method set_link.
    """

    ok = graphene.Boolean()

    @classmethod
    def set_link(cls, node1: ObjectType, node2: ObjectType):
        raise NotImplementedError("This method must be implemented in subclasses.")


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


class ParentChildEdgeMutation(EdgeMutationBase, graphene.Mutation):
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
    def mutate(cls, _: None, info: graphene.ResolveInfo,
               parent: str = "", child: str = "", **___):
        parent_, child_ = assert_input_node_types(
            info.context.shared_results,
            node1=parent,
            node2=child,
            node1_type=cls.parent_type,
            node2_type=cls.child_type
        )
        cls.set_link(parent_, child_)
        return cls(ok=True)

    @classmethod
    def set_link(cls, node1: ObjectType, node2: ObjectType):
        raise NotImplementedError("This method must be implemented in subclasses.")


class SiblingEdgeMutation(EdgeMutationBase, graphene.Mutation):
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
    def mutate(cls, _: None, info: graphene.ResolveInfo,
               node1: str = "", node2: str = "", **___):
        node1_, node2_ = assert_input_node_types(
            info.context.shared_results,
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
