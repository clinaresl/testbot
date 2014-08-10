#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# namespace.py
# Description: Generic definition of namespaces that map origin sets of any
#              cardinality onto images of an arbitrary cardinality
# -----------------------------------------------------------------------------
#
# Started on  <Wed Feb 19 18:17:04 2014 Carlos Linares Lopez>
# Last update <domingo, 10 agosto 2014 17:37:12 Carlos Linares Lopez (clinares)>
# -----------------------------------------------------------------------------
#
# $Id::                                                                      $
# $Date::                                                                    $
# $Revision::                                                                $
# -----------------------------------------------------------------------------
#
# Made by Carlos Linares Lopez
# Login   <clinares@atlas>
#

"""
Generic definition of namespaces that map origin sets of any cardinality onto
images of an arbitrary cardinality
"""

__version__  = '1.0'
__revision__ = '$Revision$'
__date__     = '$Date$'


# imports
# -----------------------------------------------------------------------------
import copy                             # for shallow copies

from collections import defaultdict
from collections import MutableMapping


# -----------------------------------------------------------------------------
# Namespace
#
# Namespaces extend dictionaries by providing additional abilities to map items
# from an origin set of any cardinality onto items of an image set of an
# arbitrary cardinality. They do effectively implement injective, surjective and
# bijective functions and generalizations of them since the same item in the
# origin set can point to an arbitrary number of items in the image set.
#
# Items in the origin set are characterized with a 'key'. Items in the image set
# are characterized with a 'component' that refers to the semantics of the
# values stored. Consider a function f:O^n -> I^m, n,m>=1, that maps
# n-dimensional tuples onto m-dimensional values: 'f' is the 'component'; 'keys'
# are required to be tuples of length 'n'; 'values' are python objects of length
# 'm'.
#
# If the keys are single values then they are accessed as ordinary attributes,
# i.e., namespace.f. Note that in this case the key is absolutely unnecessary
# since values are uniquely identified by its 'component'
#
# If the keys are multi values then they are accessed as ordinary dictionaries,
# i.e., namespace.f [key]. In this case, Namespaces can be either named or
# unnamed. By default, they are unnamed unless setkeynames is used. Advantages
# of named multi key functions are:
#
# * random access: items of the image set can be inserted by randomly accessing
#                  the keys with a dictionary with setattr
#
# * projections: Namespaces provide additional services to project subsets of
#                keys over the original set of keys for retrieving keys, values
#                and/or items.
# -----------------------------------------------------------------------------
class Namespace (MutableMapping):
    """
    Namespaces extend dictionaries by providing additional abilities to map
    items from an origin set of any cardinality onto items of an image set of an
    arbitrary cardinality. They do effectively implement injective, surjective
    and bijective functions but they do not implement generalizations of them
    since the same item in the origin set can not point to an arbitrary number
    of items in the image set ---such as in multisets.

    Items in the origin set are characterized with a 'key'. Items in the image
    set are characterized with a 'component' that refers to the semantics of the
    values stored. Consider a function f:O^n -> I^m, n,m>=1, that maps
    n-dimensional tuples onto m-dimensional values: 'f' is the 'component';
    'keys' are required to be tuples of length 'n'; 'values' are python objects
    of length 'm'.

    If the keys are single values then they are accessed as ordinary attributes,
    i.e., namespace.f. Note that in this case the key is absolutely unnecessary
    since values are uniquely identified by its 'component'

    If the keys are multi values then they are accessed as ordinary
    dictionaries, i.e., namespace.f [key]. In this case, Namespaces can be
    either named or unnamed. By default, they are unnamed unless setkeynames is
    used. Advantages of named multi key functions are:

    * random access: items of the image set can be inserted by randomly
                     accessing the keys with a dictionary with setattr

    * projections: Namespaces provide additional services to project subsets of
                   keys over the original set of keys for retrieving keys,
                   values and/or items.
    """

    def __init__ (self, **kws):
        """
        initializes the private structures of the namespace. Optionally, it
        accepts a number of assignments in the form 'attribute=value' (for
        single key attributes) or the form 'attribute={key:value}' (for multi
        key attributes). In the latter case, keys should be given as
        tuples. Otherwise, a KeyError is raised.
        """

        # initialize the list of attributes and the list of keys of every
        # multi-valued index
        self._attributes = list ()
        self._fields = defaultdict (list)

        # in case that any parameters are assigned, write them now
        for k in kws:

            # in case a dictionary has been provided like a value, then create a
            # multi key entry
            if isinstance (kws[k], dict):

                # initialize the dictionary
                object.__setattr__ (self, k, dict ())

                # and now write all values
                for (ikey, ival) in kws[k].items ():

                    # bearing in mind that keys have always to be given as
                    # tuples. If not, raise a KeyError
                    if not isinstance (ikey, tuple):
                        raise KeyError (ikey)
                    object.__getattribute__ (self, k).__setitem__ (ikey, ival)
            else:
                object.__setattr__ (self, k, kws[k])

            # add this attribute to the list of known attributes
            if k not in ['_attributes', '_fields']:
                self._attributes.append (k)


    def __setitem__ (self, attribute, value):
        """
        implement assignment to single attributes in the form
        self[attribute]=value
        """

        self.__setattr__ (attribute, value)


    def __setattr__ (self, attribute, value):
        """
        attachs the given value to the specified single-valued
        attribute. 'attribute' should be a string that uniquely identifies the
        key
        """

        # attach the value
        self.__dict__ [attribute] = value

        # and annotate it unless this is one of the protected attributes of
        # namespaces
        if (attribute not in self._attributes and
            attribute not in ['_attributes', '_fields']):
            self._attributes.append (attribute)


    def __getattr__ (self, attribute):
        """
        incidentally, this method initializes multi-key entries of Namespaces
        with the given 'attribute'
        """

        # create an empty dictionary
        object.__setattr__ (self, attribute, dict ())

        # add this attribute to the list of known attributes
        self._attributes.append (attribute)

        # and return it
        return object.__getattribute__(self, attribute)


    def __getitem__ (self, attribute):
        """
        returns the value of a single key attribute. This method provides an
        alternative access method so that a single key attribute 'attr' can be
        accessed in a namespace 'n' either as 'n.attr' or 'n [attr]'
        """

        return object.__getattribute__ (self, attribute)


    def __delattr__ (self, attribute):
        """
        implements attribute deletion. It removes an existing attribute (either
        indexed with a single or multi valued index). If the attribute does not
        exist an AttributeError is (naturally) raised
        """

        # delete the given attribute
        del self.__dict__ [attribute]

        # and remove it from the list of known attributes
        self._attributes.remove (attribute)

        # finally, in case that this was a named multi attribute, make sure to
        # remove also its keynames
        if attribute in self._fields:
            del self._fields [attribute]


    def __delitem__ (self, attribute):
        """
        implement deletion of either single or muti attributes in the form
        self[attribute]
        """

        # in fact, namespaces use interchangeably the notations .f and [f] so
        # that this service just invokes the other
        self.__delattr__ (attribute)


    def __len__ (self):
        """
        return the number of (either single or multi key) attributes in this
        namespace
        """

        # since all attributes are explicitly stored in _attributes, return the
        # length of that list. This is fairly convenient also to avoid
        # considering other attributes in self
        return len (self._attributes)


    def __contains__ (self, attribute):
        """
        implement membership test operators. Should return true if attribute is
        in self, false otherwise.
        """

        return attribute in self._attributes


    def __iter__ (self):
        """
        return an iterator over the list of attributes defined in this
        namespace. It returns both single and multi key attributes
        """

        return iter (self._attributes)


    def __repr__ (self):
        """
        shows a printable representation of the contents of this namespace
        """

        # initialization
        contents = " * Single attributes: \n"

        # first, show the contents of all single attributes in this namespace
        for attr in self:

            # in case this is a single attribute
            if not isinstance (self [attr], dict):
                contents += " \t+ %-20s : %s\n" % (attr, self[attr])

        # now, show the contents of all multi attributes in this namespace
        contents += "\n * Multi attributes: \n"
        for attr in self:

            # in case this is a multi key
            if isinstance (self [attr], dict):
                contents += "\t+ %-20s :\n" % attr

                # in case the keys of this entry are named, show the names
                if attr in self._fields:
                    contents += "\t\t key names: %s" % list (self._fields [attr])
                else:
                    contents += "\t\t key names: None"
                contents += '\n'

                # now, traverse all keys
                for ikey, ival in self [attr].items ():
                    contents += "\t\t %-20s : %s\n" % (ikey, ival)

        return contents


    def setattr (self, attribute, value, key=None):
        """
        sets a value attached to the given attribute.

        If no key is given, the attribute is assumed to be a single key
        attribute.

        The key shall be given as a dictionary. If not, an AttributeError is
        raised. Additionally, the key of the attribute shall be named as well,
        otherwise an IndexError is raised. Finally, if the dictionary given in
        key misses any of the indexes in the name of the multi key attached to
        the attribute, a KeyError is (naturally) raised
        """

        # in case the attribute is a single attribute
        if not key:

            self.__setattr__ (attribute, value)

        # else
        else:

            if not isinstance (key, dict):
                raise AttributeError (key)

            if attribute not in self._fields or not len (self._fields [attribute]):
                raise IndexError (attribute)

            # there are here two distinct cases: either the key has length 1 or
            # strictly greater than 1

            # if the key has length strictly greater than 1, then the key should
            # be represented as a tuple
            tuplekey = tuple ([key [i] for i in self._fields [attribute]])

            # otherwise, it should be represented with a scalar
            if len (tuplekey) == 1:
                index = tuplekey [0]
            else:
                index = tuplekey

            # secondly, it is highly desired to use setattr even if the index
            # does not exist ---this would ease the usage of namespaces from
            # other code
            if attribute not in self.__dict__:

                # initialize this multi-key entry
                self.__getattr__ (attribute)

            # and finally store the data
            self.__dict__ [attribute] [index] = value


    def getattr (self, attribute, key=None):
        """
        returns the value attached to a given attribute.

        If no key is given, the attribute is checked to be a single key
        attribute. If no key is given and the attribute is a multikey or does
        not exist, an AttributeError is raised.

        Otherwise, the key shall be given as a dictionary. If not, an
        AttributeError is raised. Additionally, the key of the attribute shall
        be named, otherwise an Indexerror is raised ---ie., unnamed keys are not
        supported. Finally, if the dictionary given in key misses any of the
        indexes in the name of the multi key attached to the attribute, a
        keyError is (naturally) raised
        """

        # in case the attribute is a single attribute
        if not key:

            # if either the attribute does not exist or it is not a single
            # attribute, raise an AttributeError
            if (attribute not in self.__dict__ or
                isinstance (self.__dict__ [attribute], dict)):
                raise AttributeError (attribute)

            # if here, a single attribute is guaranteed to exist so that return
            # its value
            return self.__dict__ [attribute]

        # otherwise, check that the given key is a dictionary
        if not isinstance (key, dict):
            raise AttributeError (key)

        # in case it is a dictionary, check that this attribute is named so that
        # we can *assume* that the given dictionary contains values for all
        # keynames.
        if attribute not in self._fields or not len (self._fields [attribute]):
            raise IndexError (attribute)

        # process all keys and access then the right position of the dictionary,
        # if anyone is missing Python will naturally raise an exception. There
        # are two different cases here to deal with: either the length of the
        # key is 1 or it is strictly greater than 1
        tuplekey = tuple ([key [ikey] for ikey in self.getkeynames (attribute)])

        # if the key has length 1, then the index should be represented with a
        # scalar
        if len (tuplekey) == 1:
            index = tuplekey [0]
        else:
            index = tuplekey

        # and finally return the requested data
        return self.__dict__ [attribute] [index]


    def clear (self):
        """"
        removes all attributes in this namespace restoring its original state
        """

        attributes = copy.copy (self._attributes)

        # first, delete all attributes
        for attribute in attributes:
            self.__delattr__ (attribute)

        # now, initialize the private attributes of the namespace
        self._attributes = list ()
        self._fields = defaultdict (list)


    def setkeynames (self, attribute, *keys):
        """
        give a name to all keys appearing in attribute. Note that no particular
        checking is done and it might happen that the cardinality of the keys
        and the current number of keys used does not match
        """

        self._fields [attribute] = keys


    def getkeynames (self, attribute):
        """
        return the names of all keys specified by 'attribute' or an empty list
        if the given key is unnamed or it is not indexed by multiple keys
        """

        # check that attribute is a multi key attribute
        if attribute not in self._fields:
            return []

        return self._fields [attribute]


    def keys (self, attribute, *keys):
        """
        returns the projection of the keys of attribute over the specified
        subset of keys. If none is given, all are used by default. If the given
        attribute is not indexed by a named multi key an AttributeError is
        raised

        In general, keys (f) is safer than f.keys () since it is
        order-preserving
        """

        # check that attribute is a multi key attribute
        if attribute not in self._fields:
            raise AttributeError (attribute)

        # use all keys by default is none is specified
        if not keys: keys = self._fields [attribute]

        # note that items are sorted so that they are always traversed in the
        # same order in spite of the component requested at different methods
        result = list ()
        for (ikey, ival) in sorted (self.__dict__ [attribute].items ()):
            result.append (tuple ([ikey[i] for i in
                                   [self._fields [attribute].index(j) for j in keys]]))

        return result


    def values (self, attribute):
        """
        returns the values of the given multi key attribute. If the given
        attribute is not indexed by a named multi key an AttributeError is
        raised

        In general, values (f) is safer than f.values () since it is
        order-preserving
        """

        # check that attribute is a multi key attribute
        # if attribute not in self._fields:
        #     raise AttributeError (attribute)

        # note that items are sorted so that they are always traversed in the
        # same order in spite of the component requested at different methods
        return [item[1] for item in sorted (self.__dict__ [attribute].items ())]


    def items (self, attribute, *keys):
        """
        returns a list of tuples (key, value) where key is the projection of the
        keys of the attribute over 'keys'. If no keys are provided then all are
        used by default. If the given attribute is not indexed by a named multi
        key an AttributeError is raised

        In general, items (f) is safer than f.items () since it is
        order-preserving
        """

        # check that attribute is a multi key attribute
        if attribute not in self._fields:
            raise AttributeError (attribute)

        # use all keys by default is none is specified
        if not keys: keys = self._fields [attribute]

        # note that items are sorted so that they are always traversed in the
        # same order in spite of the component requested at different methods
        result = list ()
        for (ikey, ival) in sorted (self.__dict__ [attribute].items ()):
            result.append ((tuple ([ikey[i] for i in
                                    [self._fields [attribute].index(j) for j in keys]]), ival))

        return result


    def update (self, *args):
        """
        updates destructively (ie., overwriting if necessary) the contents of
        the given attribute with the information given in args. 'args' shall be
        other namespaces. This service can be used for updating both single and
        multi key entries.

        Single key entries: this service updates all single key entries given in
        other namespaces. If this namespace contains entries with the same
        name than those given in args, then they are overwritten.

        Multi key entries: this service updates all multi key entries given in
        another namespaces copying (and even overwritting) the name keys if they
        are present in the other namespace. Again, note that this service does
        not check that the cardinality of the keys matches the cardinality of
        existing keys if the attribute already exists.

        if an arg is not a namespace, a TypeError is raised
        """

        for iarg in args:

            # check the type of this argument, if not a namespace, raise a
            # TypeError
            if not isinstance (iarg, Namespace):
                raise TypeError (iarg)

            # traverse all attributes in this namespace
            for iattr in iarg:

                # in case this is a single key attribute, just copy it
                if not isinstance (iarg [iattr], dict):
                    setattr (self, iattr, iarg [iattr])

                # otherwise,
                else:

                    # in case this attribute does not exist in this
                    # namespace, then initialize it
                    if iattr not in self:
                        object.__setattr__ (self, iattr, dict ())

                    # traverse all items appearing in the other namespace
                    # ---note that direct access to the underlying dict is
                    # implemented because the service 'items' provided in
                    # namespaces is valid only for performing projections (ie,
                    # for *named* multi key attributes)
                    for (ikey, ival) in iarg [iattr].items ():
                        object.__getattribute__ (self, iattr) [ikey] = ival

                    # and add this attribute to the list of known attributes in
                    # case it was just created. Also, copy the keynames if
                    # present
                    if iattr not in self._attributes:
                        self._attributes.append (iattr)

                    if iarg.getkeynames (iattr):
                        self.setkeynames (iattr, *iarg.getkeynames (iattr))


if __name__ != '__main__':

    # create a new namespace
    sys = Namespace ()

    # populate it with single values attached to single keys
    sys.cputime = 9.89
    sys.wctime = 10.02
    sys.vsize = 107.86
    sys.time = "2014-02-19 21:46:02.556"

    # multi values attached to single keys
    sys.plan_length = [43, 39, 16, 15]
    sys.cost = [52, 43, 18, 16]

    # populate it with single values attached to multi keys
    sys.expanded_nodes [(10, 36)] = 2
    sys.expanded_nodes [(10, 37)] = 8
    sys.expanded_nodes [(11, 36)] = 10
    sys.expanded_nodes [(11, 37)] = 45

    # populate it with multi values attached to multi keys
    sys.val_results [('cgamer', 'parking', '000')] = ['Valid', 'Processed', 102, 89]
    sys.val_results [('cgamer', 'parking', '001')] = ['Valid', 'Processed', 117, 115]
    sys.val_results [('cgamer', 'parking', '002')] = ['', 'Unprocessed', -1, -1]
    sys.val_results [('cgamer', 'parking', '003')] = ['Invalid', 'Processed', -1, -1]

    # now, name the multi-key attributes ---based on collection.namedtuples
    sys.setkeynames ('expanded_nodes', 'depth', 'f')
    sys.setkeynames ('val_results', 'planner', 'domain', 'problem')

    # since the latest attributes are named it is now possible to set values
    # naming the keys with a dictionary sys.setattr
    sys.setattr ('expanded_nodes', key={'depth': 12, 'f': 36}, value=58)
    sys.setattr ('expanded_nodes', key={'depth': 12, 'f': 37}, value=319)

    sys.setattr ('val_results', key={'domain': 'pegsol',
                                     'planner': 'lama-2011',
                                     'problem':'000'},
                                     value=['Valid', 'Processed', 217, 193])
    sys.setattr ('val_results', key={'domain': 'pegsol',
                                     'planner': 'lama-2011',
                                     'problem':'001'},
                                value=['Valid', 'Processed', 206, 188])

    # populate it with single values attached to multi keys
    sys.generated_nodes [(10, 36)] = 2
    sys.generated_nodes [(10, 37)] = 8
    sys.generated_nodes [(11, 36)] = 10
    sys.generated_nodes [(11, 37)] = 45

    # testing the update procedure
    tests = Namespace ()

    # populate it with data which clashes with sys.expanded_nodes
    tests.expanded_nodes [(10, 36)] = 12
    tests.expanded_nodes [(10, 37)] = 18
    tests.expanded_nodes [(11, 36)] = 110
    tests.expanded_nodes [(11, 37)] = 145

    tests.setkeynames ('expanded_nodes', 'a', 'b')



# Local Variables:
# mode:python
# fill-column:80
# End:
