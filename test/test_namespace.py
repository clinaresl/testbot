#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# test_namespace.py
# Description: unittest of namespaces
# -----------------------------------------------------------------------------
#
# Started on  <Fri Feb 21 08:22:32 2014 Carlos Linares Lopez>
# Last update <martes, 11 marzo 2014 12:16:31 Carlos Linares Lopez (clinares)>
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
.. module:: test_namespace
   :platform: Linux
   :synopsis: unittest of namespaces

.. moduleautor:: Carlos Linares Lopez <carlos.linares@uc3m.es>
"""


__version__  = '1.0'
__revision__ = '$Revision$'
__date__     = '$Date$'


# imports
# -----------------------------------------------------------------------------
import namespace                # unit to test
import random                   # random operations
import string                   # direct access to string sets
import sys                      # maxint
import unittest                 # unit test facilities


# -----------------------------------------------------------------------------
# mkeint
#
# return a random integer value
# -----------------------------------------------------------------------------
def mkeint ():
    """
    return a random integer value
    """

    return int (random.randint (0, sys.maxint) - random.randint (0, sys.maxint))


# -----------------------------------------------------------------------------
# mkedouble
#
# return a random floating point value
# -----------------------------------------------------------------------------
def mkedouble ():
    """
    return a random floating point value
    """

    return float (((random.randint (0, sys.maxint) - random.randint (0, sys.maxint)) /
                   (1.0 * random.randint (0, sys.maxint)) -
                   (random.randint (0, sys.maxint) - random.randint (0, sys.maxint)) /
                   (1.0 * random.randint (0, sys.maxint))))


# -----------------------------------------------------------------------------
# mkestr
#
# return a random string value with a length chosen from a normal distribution
# with mean mu and variance sigma. The resulting strings are not quoted
# -----------------------------------------------------------------------------
def mkestr (mu=5, sigma=00):
    """
    return a random string value with a length chosen from a normal distribution
    with mean mu and variance sigma. The resulting strings are not quoted
    """

    prefix = random.choice (string.ascii_uppercase)
    suffix = ''.join ([random.choice(string.ascii_uppercase +
                                     string.ascii_lowercase +
                                     string.digits)
                                     for x in range(int (random.gauss (mu, sigma)))])

    return str (prefix + suffix)


# -----------------------------------------------------------------------------
# randval
#
# return a random instance of a rand type among those specified in the given
# list 'types'. Allowed values for this list are 'int', 'double' and 'str'. If
# no types are given, it is automatically initizialized with all of these. If
# the chosen type is not among these, a ValueError is raised
# -----------------------------------------------------------------------------
def randval (*types):
    """
    return a random instance of a rand type among those specified in the given
    list 'types'. Allowed values for this list are 'int', 'double' and 'str'. If
    no types are given, it is automatically initizialized with all of these. If
    the chosen type is not among these, a ValueError is raised
    """

    if not types:
        types = ['int', 'double', 'str']

    # pick up a random type
    randtype = types [random.randint (0, sys.maxint) % len (types)]

    # and return a random value of this type
    if randtype == 'int':
        return mkeint ()
    elif randtype == 'double':
        return mkedouble ()
    elif randtype == 'str':
        return mkestr ()

    # if the random type is not among this, raise a ValueError
    raise ValueError (randtype)


# -----------------------------------------------------------------------------
# mkelist
#
# return a list with instances from the specified types whose length is chosen
# from a normal distribution with mean mu and variance sigma. If no types are
# specified, all of them are used
# -----------------------------------------------------------------------------
def mkelist (mu=100, sigma=10, *types):
    """
    return a list with instances from the specified types whose length is chosen
    from a normal distribution with mean mu and variance sigma. If no types are
    specified, all of them are used
    """

    # initialization
    result = list ()

    # in case that no types are specified, use them all
    if not types:
        types = ['int', 'double', 'str']

    # and now return the list randomly generated with instances from the
    # specified types
    return [randval (*types)
            for ith in range (0, int (random.gauss (mu, sigma)))]


# -----------------------------------------------------------------------------
# mketuple
#
# return a tuple with instances from the specified types whose length is chosen
# from a normal distribution with mean mu and variance sigma. If no types are
# specified, all of them are used
# -----------------------------------------------------------------------------
def mketuple (mu=100, sigma=10, *types):
    """
    return a tuple with instances from the specified types whose length is
    chosen from a normal distribution with mean mu and variance sigma. If no
    types are specified, all of them are used
    """

    # use the random creation of lists to randomly generate tuples
    return tuple (mkelist (mu, sigma, *types))


# -----------------------------------------------------------------------------
# mkedict
#
# return a dict whose values are instances from the specified types whose length
# is chosen from a normal distribution with mean mu and variance sigma. If no
# types are specified, all of them are used
# -----------------------------------------------------------------------------
def mkedict (mu=100, sigma=10, *types):
    """
    return a dict whose values are instances from the specified types whose
    length is chosen from a normal distribution with mean mu and variance
    sigma. If no types are specified, all of them are used
    """

    # initialization
    result = dict ()

    # in case that no types are specified, use them all
    if not types:
        types = ['int', 'double', 'str']

    # and now return the dictionary randomly generated with instances from the
    # specified types (note that keys are always strings)
    return dict ([(randval ('str'), randval (*types))
                  for ith in range (0, int (random.gauss (mu, sigma)))])


# -----------------------------------------------------------------------------
# SingleTestCase
#
# tests that namespaces are writable in the same way they are expected. This
# test includes only single key attributes with single values
# -----------------------------------------------------------------------------
class SingleTestCase(unittest.TestCase):
    """
    tests that namespaces are writable in the same way they are expected. This
    test includes only single key attributes with single values
    """

    # static defs
    # -------------------------------------------------------------------------
    _mean = 1000                # statistical params used for generating samples
    _variance = 100

    def setUp (self):
        """
        define a particular test case
        """

        # set up a particular test with single key entries. These are
        # represented as random dictionaries which hold the attribute in the key
        # and its value in the right term of the dictionary
        self._testcase = mkedict (SingleTestCase._mean, SingleTestCase._variance)

        # create a namespace
        self._namespace = namespace.Namespace ()

        # populate the namespace randomly
        for (attribute, value) in self._testcase.items ():

            if (isinstance (value, str)):
                exec  ("self._namespace.%s = '%s'" % (attribute, value))

            else:
                exec  ("self._namespace.%s = %s" % (attribute, value))


    def test_single_init (self):
        """
        tests that single key attributes of namespaces can be initialized with
        iterables of the form attr=value
        """

        # python2.7 does not allow to pass more than 255 args, so the direct
        # initialization is just tested with a different test set with 200 args
        testcase = mkedict (200, 0)

        # create a specification string that actually specifies all contents of
        # this test case in the form 'attr : value'
        cmd = ''
        for ikey, ival in testcase.items ():
            if type (ival)==str:
                cmd += "%s = '%s', " % (ikey, ival)
            else:
                cmd += "%s = %s, " % (ikey, ival)

        # now, create a namespace passing by this command line specification
        exec ("test = namespace.Namespace (%s)" % cmd[:-2])

        # check now that all values are correct using item selection, attribute
        # names and getattr
        for ikey, ival in testcase.items ():

            for imethod in ["test ['%s']" % ikey,               # item selection
                            "test.%s" % ikey,                   # attribute naming
                            "test.getattr ('%s')" % ikey]:      # getattr

                # compute the expected and returned values
                (expected, returned) = (ival, eval (imethod))

                # and check for equality
                if isinstance (ival, float):
                    self.assertAlmostEqual (expected, returned)
                else:
                    self.assertEqual (expected, returned)


    def test_single_write_attribute_naming (self):
        """
        test that namespaces are writable with single key values using attribute
        naming. Data is verified reading the namespace using item selection,
        attribute naming and getattr
        """

        # create a namespace
        inamespace = namespace.Namespace ()

        # populate the namespace with the info in this testcase
        for ikey, ival in self._testcase.items ():

            if (isinstance (ival, str)):
                exec  ("inamespace.%s = '%s'" % (ikey, ival))

            else:
                exec  ("inamespace.%s = %s" % (ikey, ival))

        # now, verify that the values stored in the namespace are correct
        for ikey, ival in self._testcase.items ():

            # access data using item selection, attribute naming and getattr
            for imethod in ["inamespace ['%s']" % ikey,           # item selection
                            "inamespace.%s" % ikey,               # attribute naming
                            "inamespace.getattr ('%s')" % ikey]:  # getattr

                # compute the expected and returned values
                (expected, returned) = (ival, eval (imethod))

                # and check for equality
                if isinstance (ival, float):
                    self.assertAlmostEqual (expected, returned)
                else:
                    self.assertEqual (expected, returned)


    def test_single_write_item_selection (self):
        """
        test that namespaces are writable with single key values using item
        selection. Data is verified reading the namespace using item selection,
        attribute naming and getattr
        """

        # create a namespace
        inamespace = namespace.Namespace ()

        # populate the namespace with the info in this testcase
        for ikey, ival in self._testcase.items ():

            if (isinstance (ival, str)):
                exec  ("inamespace ['%s'] = '%s'" % (ikey, ival))

            else:
                exec  ("inamespace ['%s'] = %s" % (ikey, ival))

        # now, verify that the values stored in the namespace are correct
        for ikey, ival in self._testcase.items ():

            # access data using item selection, attribute naming and getattr
            for imethod in ["inamespace ['%s']" % ikey,           # item selection
                            "inamespace.%s" % ikey,               # attribute naming
                            "inamespace.getattr ('%s')" % ikey]:  # getattr

                # compute the expected and returned values
                (expected, returned) = (ival, eval (imethod))

                # and check for equality
                if isinstance (ival, float):
                    self.assertAlmostEqual (expected, returned)
                else:
                    self.assertEqual (expected, returned)


    def test_single_write_setattr (self):
        """
        test that namespaces are writable with single key values using
        setattr. Data is verified reading the namespace using item selection,
        attribute naming and getattr
        """

        # create a namespace
        inamespace = namespace.Namespace ()

        # populate the namespace with the info in this testcase
        for ikey, ival in self._testcase.items ():

            if (isinstance (ival, str)):
                exec  ("inamespace.setattr ('%s', '%s')" % (ikey, ival))

            else:
                exec  ("inamespace.setattr ('%s', %s)" % (ikey, ival))

        # now, verify that the values stored in the namespace are correct
        for ikey, ival in self._testcase.items ():

            # access data using item selection, attribute naming and getattr
            for imethod in ["inamespace ['%s']" % ikey,           # item selection
                            "inamespace.%s" % ikey,               # attribute naming
                            "inamespace.getattr ('%s')" % ikey]:  # getattr

                # compute the expected and returned values
                (expected, returned) = (ival, eval (imethod))

                # and check for equality
                if isinstance (ival, float):
                    self.assertAlmostEqual (expected, returned)
                else:
                    self.assertEqual (expected, returned)


    def test_single_membership (self):
        """
        test membership of single key values in namespaces
        """

        # create a list with attributes that are very likely not in the
        # namespace, add it to the list of attributes in the namespace and
        # shuffle it all
        tstlist = mkelist (SingleTestCase._mean, SingleTestCase._variance, 'str') + \
          self._testcase.keys ()
        random.shuffle (tstlist)

        # for all attributes
        for attribute in tstlist:

            # check membership
            self.assertEqual (eval ("'%s' in self._namespace" % attribute),
                              attribute in self._namespace)


    def test_single_iter (self):
        """
        test iterators over the single keys of this namespace
        """

        # initialization
        nbattrs = 0

        # first, check that all attributes returned by the iterator over the
        # namespace are in the current test case. In passing, compute the number
        # of attributes traversed
        for iattribute in self._namespace:

            nbattrs += 1
            self.assertTrue (iattribute in self._testcase)

        # before leaving, make sure that *all* attributes were traversed
        self.assertEqual (nbattrs, len (self._testcase))
        self.assertEqual (nbattrs, eval ("len (self._namespace)"))


    def test_single_len (self):
        """
        test that the length of a namespace is correctly computed
        """

        # just compare the length of the namespace as computed by namespace and
        # the number of items inserted in it
        self.assertEqual (eval ("len (self._namespace)"),
                          len (self._testcase))


    def test_single_delete_attribute_naming (self):
        """
        verify that single attributes are removed from the namespace when
        specified using attribute naming
        """

        # now, verify that the values stored in the namespace are correct
        for ikey in self._testcase.keys ():

            # delete this attribute from the namespace
            exec ("del self._namespace.%s" % ikey)

            # now, verify that it does not exist in the namespace anymore
            self.assertNotIn (ikey, self._namespace)

        # additionally, verify that the namespace is empty
        self.assertEqual (eval ("len (self._namespace)"), 0)


    def test_single_delete_item_selection (self):
        """
        verify that single attributes are removed from the namespace when
        specified using item selection
        """

        # now, verify that the values stored in the namespace are correct
        for ikey in self._testcase.keys ():

            # delete this attribute from the namespace
            exec ("del self._namespace ['%s']" % ikey)

            # now, verify that it does not exist in the namespace anymore
            self.assertNotIn (ikey, self._namespace)

        # additionally, verify that the namespace is empty
        self.assertEqual (eval ("len (self._namespace)"), 0)


    def test_single_clear (self):
        """
        test that the namespace is properly cleared when requested
        """

        # first, request clearing the namespace
        exec ("self._namespace.clear ()")

        # now, check that it contains zero items
        self.assertEqual (eval ("len (self._namespace)"), 0)

        # now, ensure that all attributes that were previously inserted are not
        # available anymore
        for attribute in self._testcase.keys ():

            self.assertEqual (eval ("'%s' in self._namespace" % attribute), False)


    def test_single_update (self):
        """
        check that namespaces can be updated with other namespace
        """

        # python2.7 does not allow to pass more than 255 args, so the direct
        # initialization is just tested with a different test set with 200 args
        testcase = mkedict (200, 0)

        # create a specification string that actually specifies all contents of
        # this test case in the form 'attr : value'
        cmd = ''
        for ikey, ival in testcase.items ():
            if type (ival)==str:
                cmd += "%s = '%s', " % (ikey, ival)
            else:
                cmd += "%s = %s, " % (ikey, ival)

        # now, create a namespace passing by this command line specification
        exec ("test = namespace.Namespace (%s)" % cmd[:-2])

        # update the testcase in this instance with this namespace
        exec ("self._namespace.update (test)")

        # check now that all values in test are in this instance
        for ikey, ival in testcase.items ():

            # ---item selection
            (expected, returned) = (ival, eval ("test ['%s']" % ikey))

            # check for equality
            if isinstance (expected, float):
                self.assertAlmostEqual (expected, returned)
            else:
                self.assertEqual (expected, returned)

        # verify also that all items originally in the testcase are still there
        for (attribute, value) in self._testcase.items ():

            # compute separately, the expected value and the returned value
            (expected, returned) = (value, eval ("self._namespace.%s" % attribute))

            # check for equality
            if isinstance (expected, float):
                self.assertAlmostEqual (expected, returned)
            else:
                self.assertEqual (expected, returned)


    def tearDown (self): pass


def namekeys (testcase, Failure=False):
    """
    this method set keynames to all the attributes in testcase in such a way
    that an exception shall be raised if Failure is True. Otherwise, the
    assignment shall be sound. The names are given in the order of the keys
    """

    # initialization - the following dictionary contains the keys of all
    # multi key attributes
    keynames = dict ()

    # for all attributes of this namespace
    for attribute in testcase.keys ():

        # create keynames which are just tuples of strings. If a Failure is
        # requested then create a tuple which is longer than the number of
        # keys, otherwise, create a tuple of strings which matches the
        # number of keys. All keys are assumed to be of the same length and
        # thus the first one is used
        if Failure:
            keynames [attribute] = mketuple (len (testcase [attribute].keys () [0]) + 1, 0.0,
                                             'str')
        else:
            keynames [attribute] = mketuple (len (testcase [attribute].keys () [0]), 0.0, 'str')

    # and return the keynames for all attributes of this class
    return keynames


def filterkeys (keynames, keyspec, row):
    """
    returns the values in row according to keyspec. 'keynames' contains the
    names of every entry in 'row' and 'keyspec' indicates the names of those
    that have to be filtered (ie., accepted). The output shall be given in the
    order specified in 'keyspec'
    """

    # initialization
    result = list ()

    # process the terms in keyspec in the same order they are given
    for ikey in keyspec:
        result.append (row [keynames.index (ikey)])

    # and return the list
    return result


# -----------------------------------------------------------------------------
# MultipleTestCase
#
# tests that namespaces are writable in the same way they are expected. This
# test includes only (named and unnamed) multi key attributes with single values
# -----------------------------------------------------------------------------
class MultipleTestCase(unittest.TestCase):
    """
    tests that namespaces are writable in the same way they are expected. This
    test includes only (named and unnamed) multi key attributes with single
    values
    """

    # static defs
    # -------------------------------------------------------------------------
    _mean = 40                  # statistical params used for generating samples
    _variance = 10

    _precision = 1000.0         # log (_precision) is the number of digits used
                                # when comparing floats

    def setUp (self):
        """
        define a particular test case
        """

        # set up a particular test with multiple key entries. The data of the
        # whole test case is stored in two nested dictionaries. The first key is
        # the name of an unnamed multi key atttribute. It contains another
        # dictionary which is indexed by a tuple of strings and/or ints which
        # stores values of different types ---but all being single valued

        # first, _testcase contains the attributes, its values (randomly
        # generated) will be next overriden
        self._testcase = mkedict (MultipleTestCase._mean,
                                  MultipleTestCase._variance)

        for attribute in self._testcase:
            self._testcase [attribute] = dict ()

            # compute randomly the number of keys used to index this entry
            # ---note that the following statement forces the key to contain at
            # least one element
            keylength = max (1, int (random.gauss (MultipleTestCase._mean,
                                                   MultipleTestCase._variance)))

            # now, compute a random number of entries for this attribute ---note
            # that the following statement forces at least one entry
            for ientry in range(max (1, int (random.gauss (MultipleTestCase._mean,
                                                           MultipleTestCase._variance)))):

                # compute randomly the key of this entry as a tuple
                key = mketuple (keylength, 0, 'int', 'str')

                # checking the length of the keys is pretty important since
                # namespaces do not verify it
                if keylength != len (key):
                    raise KeyError ('Mismatch in the length of the key: %i != %i' % (keylength, len (key)))

                # and write it into the specification of this testcase
                self._testcase [attribute][key] = randval ()

        # create a namespace
        self._namespace = namespace.Namespace ()

        # populate the namespace randomly
        for attribute in self._testcase.keys ():

            for (ikey, ivalue) in self._testcase [attribute].items ():

                if (isinstance (ivalue, str)):
                    exec  ("self._namespace.%s [%s] = '%s'" % (attribute, ikey, ivalue))

                else:
                    exec  ("self._namespace.%s [%s] = %s" % (attribute, ikey, ivalue))


    def test_multi_init (self):
        """
        test the initialization service for multi-valued attributes using
        dictionaries
        """

        # now, initialize a namespace passing the contents of the namespace
        # defined in setUp
        cmd = ''
        for iattr in self._testcase.keys ():
            cmd += "%s = %s, " % (iattr, self._testcase[iattr])

        # now, create a namespace passing by this command line specification
        exec ("test = namespace.Namespace (%s)" % cmd[:-2])

        # finally, verify that all data was correctly saved using both item
        # selection and attribute names
        for iattr in self._testcase.keys ():

            for ikey, ival in self._testcase [iattr].items ():

                for imethod in ["test ['%s'] [%s]" % (iattr, ikey),  # item selection
                                "test.%s [%s]" % (iattr, ikey)]:     # attribute naming

                    (expected, returned) = (ival, eval (imethod))

                    # check for equality
                    if isinstance (ival, float):
                        self.assertAlmostEqual (expected, returned)
                    else:
                        self.assertEqual (expected, returned)


    def test_multi_write_attribute_naming (self):
        """
        test that namespaces are writable with unnamed multi attributes using
        attribute naming. Data is verified using both attribute naming and item
        selection
        """

        # create a namespace
        inamespace = namespace.Namespace ()

        # populate the namespace randomly
        for attribute in self._testcase.keys ():

            for (ikey, ivalue) in self._testcase [attribute].items ():

                if (isinstance (ivalue, str)):
                    exec  ("inamespace.%s [%s] = '%s'" % (attribute, ikey, ivalue))

                else:
                    exec  ("inamespace.%s [%s] = %s" % (attribute, ikey, ivalue))

        # finally, verify that all data was correctly saved using both item
        # selection and attribute names
        for iattr in self._testcase.keys ():

            for ikey, ival in self._testcase [iattr].items ():

                for imethod in ["inamespace ['%s'] [%s]" % (iattr, ikey),  # item selection
                                "inamespace.%s [%s]" % (iattr, ikey)]:     # attribute naming

                    (expected, returned) = (ival, eval (imethod))

                    # check for equality
                    if isinstance (ival, float):
                        self.assertAlmostEqual (expected, returned)
                    else:
                        self.assertEqual (expected, returned)


    def test_multi_write_item_selection (self):
        """
        test that namespaces are writable with unnamed multi attributes using
        item selection. Note that for this to work, multi attributes have to be
        first declared. Data is verified using both attribute naming and item
        selection
        """

        # create a namespace
        inamespace = namespace.Namespace ()

        # populate the namespace randomly
        for attribute in self._testcase.keys ():

            # to enable writes using item selection the multi attribute has to
            # be first declared
            exec ("inamespace.%s" % attribute)

            for (ikey, ivalue) in self._testcase [attribute].items ():

                if (isinstance (ivalue, str)):
                    exec  ("inamespace ['%s'] [%s] = '%s'" % (attribute, ikey, ivalue))

                else:
                    exec  ("inamespace ['%s'] [%s] = %s" % (attribute, ikey, ivalue))

        # finally, verify that all data was correctly saved using both item
        # selection and attribute names
        for iattr in self._testcase.keys ():

            for ikey, ival in self._testcase [iattr].items ():

                for imethod in ["inamespace ['%s'] [%s]" % (iattr, ikey),  # item selection
                                "inamespace.%s [%s]" % (iattr, ikey)]:     # attribute naming

                    (expected, returned) = (ival, eval (imethod))

                    # check for equality
                    if isinstance (ival, float):
                        self.assertAlmostEqual (expected, returned)
                    else:
                        self.assertEqual (expected, returned)


    def test_multi_delete_attribute_naming (self):
        """
        verify that multi attributes are removed from the namespace when
        specified using attribute naming
        """

        # now, verify that the values stored in the namespace are correct
        for ikey in self._testcase.keys ():

            # delete this attribute from the namespace
            exec ("del self._namespace.%s" % ikey)

            # now, verify that it does not exist in the namespace anymore
            self.assertNotIn (ikey, self._namespace)

        # additionally, verify that the namespace is empty
        self.assertEqual (eval ("len (self._namespace)"), 0)


    def test_multi_delete_item_selection (self):
        """
        verify that multi attributes are removed from the namespace when
        specified using item selection
        """

        # now, verify that the values stored in the namespace are correct
        for ikey in self._testcase.keys ():

            # delete this attribute from the namespace
            exec ("del self._namespace ['%s']" % ikey)

            # now, verify that it does not exist in the namespace anymore
            self.assertNotIn (ikey, self._namespace)

        # additionally, verify that the namespace is empty
        self.assertEqual (eval ("len (self._namespace)"), 0)


    def test_multi_membership (self):
        """
        test membership of unnamed multi key values in namespaces
        """

        # create a list with attributes that are very likely not in the
        # namespace, add it to the list of attributes in the namespace and
        # shuffle it all
        tstlist = mkelist (SingleTestCase._mean, SingleTestCase._variance, 'str') + \
          self._testcase.keys ()
        random.shuffle (tstlist)

        # for all attributes
        for attribute in tstlist:

            # check membership
            self.assertEqual (eval ("'%s' in self._namespace" % attribute),
                              attribute in self._namespace)


    def test_multi_iter (self):
        """
        test iterators over the unnamed multi keys of this namespace
        """

        # initialization
        nbattrs = 0

        # first, check that all attributes returned by the iterator over the
        # namespace are in the current test case. In passing, compute the number
        # of attributes traversed
        for iattribute in self._namespace:

            nbattrs += 1
            self.assertTrue (iattribute in self._testcase)

        # before leaving, make sure that *all* attributes were traversed
        self.assertEqual (nbattrs, len (self._testcase))
        self.assertEqual (nbattrs, eval ("len (self._namespace)"))


    def test_multi_len (self):
        """
        test that the length of a namespace is correctly computed
        """

        # just compare the length of the namespace as computed by namespace and
        # the number of items inserted in it
        self.assertEqual (eval ("len (self._namespace)"),
                          len (self._testcase))


    def test_multi_clear (self):
        """
        test that the namespace is properly cleared when requested
        """

        # first, request clearing the namespace
        exec ("self._namespace.clear ()")

        # now, check that it contains zero items
        self.assertEqual (eval ("len (self._namespace)"), 0)

        # now, ensure that all attributes that were previously inserted are not
        # available anymore
        for attribute in self._testcase.keys ():

            self.assertFalse (eval ("'%s' in self._namespace" % attribute))


    def test_multi_keynames (self):
        """
        test that multi key attributes are by default unnamed and that they can
        be given arbitrary keys that can be correctly accessed
        """

        # first, traverse all the attributes of this namespace and check that
        # the result of getkeynames is an empty list
        for attribute in self._testcase.keys ():

            self.assertFalse (eval ("self._namespace.getkeynames ('%s')" % attribute))

        # next, compute keynames for all keys of all attributes such that they are
        # known to be correct
        keynames = namekeys (self._testcase, Failure=False)

        # set the key names over all attributes of this test case
        for attribute in self._testcase:

            exec ("self._namespace.setkeynames ('%s', *%s)" % (attribute, keynames [attribute]))

        # and now, check that all keys have been properly set
        for attribute in self._testcase:

            returned = eval ("self._namespace.getkeynames ('%s')" % attribute)
            self.assertEqual (returned, keynames [attribute])


    def test_multi_setattr (self):
        """
        test that named multi key attributes can be set using the setattr
        service (ie., using dictionaries that access the keys randomly)
        """

        # compute keynames for all keys of all attributes such that they are
        # known to be correct
        keynames = namekeys (self._testcase, Failure=False)

        # set the key names over all attributes of this test case
        for attribute in self._testcase:

            exec ("self._namespace.setkeynames ('%s', *%s)" % (attribute, keynames [attribute]))

        # now, try setting random values using setattr for all attributes. Only
        # one value is written per multi key attribute
        expected = dict ()
        keys = dict ()
        for attribute in self._testcase:

            # first, compute a dictionary of random values for all
            # keys. 'values' contains the values of all keys used to access this
            # entry of the namespace; 'keys' is the dictionary that contains
            # pairs of the form (key, value) used to selectively access this
            # attribute of the namespace; 'expected' contains the value written
            # which is expected to be retrieved in the next loop.
            values = [randval () for ith in range (len (keynames [attribute]))]
            keys [attribute] = dict (zip (keynames [attribute], values))
            expected [attribute] = randval ()

            if isinstance (expected [attribute], str):
                exec ("self._namespace.setattr ('%s', '%s', keys [attribute])"
                      % (attribute, expected [attribute]))
            else:
                exec ("self._namespace.setattr ('%s', %s, keys [attribute])"
                      % (attribute, expected [attribute]))

            # also, add this value to the testset since it will be verified when
            # using keys below
            self._testcase [attribute][tuple (values)] = expected [attribute]


        # finally, retrieve data to make sure that it was written properly using
        # two different methods, on one hand getattr (), on the other hand,
        # using keys ()

        # ---using getattr
        for attribute in self._testcase:

            # read the value previously stored at this entry
            returned = eval ("self._namespace.getattr ('%s', keys [attribute])" % attribute)

            # check for equality
            if isinstance (expected [attribute], float):
                self.assertAlmostEqual (returned, expected [attribute])
            else:
                self.assertEqual (returned, expected [attribute])


        # ---using keys
        for attribute in self._testcase:

            # retrieve all the keys used for indexing values in this multi key
            # attribute
            returnedkeys = eval ("self._namespace.keys ('%s')" % attribute)

            # and now traverse them all checking that they hold the correct
            # values
            for ikey in returnedkeys:

                # retrieve the value and compare it to the expected value
                returned = eval ("self._namespace.%s [%s]" % (attribute, ikey))
                expected = self._testcase [attribute][ikey]

                # check for equality
                if isinstance (expected, float):
                    self.assertAlmostEqual (returned, expected)
                else:
                    self.assertEqual (returned, expected)


    def test_multi_keys (self):
        """
        test the projection of multi keys over a selected subset of them
        """

        # compute keynames for all keys of all attributes such that they are
        # known to be correct
        keynames = namekeys (self._testcase, Failure=False)

        # set the key names over all attributes of this test case
        for attribute in self._testcase:

            exec ("self._namespace.setkeynames ('%s', *%s)" % (attribute, keynames [attribute]))

            # now, compute a particular mask for these key names choosing
            # randomly every key
            while True:
                keyspec = [keynames [attribute][jkey]
                           for jkey in range (0, len (keynames [attribute]))
                           if int (random.uniform (0, 2)) == 1]
                if keyspec: break
            random.shuffle (keyspec)

            # perform the projection of all entries of this attribute over the
            # set of keys selected in keyspec and in the same order
            returned = eval ("self._namespace.keys ('%s', *keyspec)" % (attribute))

            # now, compute the same set manually
            expected = list ()
            for ikey in self._testcase [attribute].keys ():

                # compute by hand the projection of keys over keyspec
                expected.append (tuple (filterkeys (list (keynames [attribute]), keyspec, ikey)))

            # make sure that they both are equal
            self.assertItemsEqual (expected, returned)


    def test_multi_values (self):
        """
        test that all values of a multi key attribute are correctly returned
        """

        # for every attribute
        for attribute in self._testcase:

            # request the namespace to return all values for this attribute and
            # retrieve the same values from the testcase
            returned = eval ("self._namespace.values ('%s')" % attribute)
            expected = self._testcase[attribute].values ()

            # just verify that they are strictly the same ---because floats have
            # to be rounded, both lists are processed first. Note that floats
            # are here rounded to the precision given by the static variable
            # _precision
            lret = map (lambda iret:(int (iret*MultipleTestCase._precision)) /
                        MultipleTestCase._precision
                        if isinstance (iret, float) else iret, returned)
            lexp = map (lambda iexp:(int (iexp*MultipleTestCase._precision)) /
                        MultipleTestCase._precision
                        if isinstance (iexp, float) else iexp, expected)

            # and now check that both lists are the same (in spite of the order
            # of its items)
            self.assertItemsEqual (lret, lexp)


    def test_multi_update (self):
        """
        check that namespaces can be updated with other namespace
        """

        # internal attributes for the random generation of different structures
        (mean, variance) = (50, 0)

        # create a random collection of multi-key attributes
        testcase = mkedict (mean, variance)

        # now, for every attribute create an additional dictionary that holds
        # the multi-key values
        for attribute in testcase:
            testcase [attribute] = dict ()

            # compute randomly the number of keys used to index this entry
            # ---note that the following statement forces the key to contain at
            # least one element
            keylength = max (1, int (random.gauss (mean, variance)))

            # now, compute a random number of entries for this attribute ---note
            # that the following statement forces at least one entry
            for ientry in range(max (1, int (random.gauss (mean, variance)))):

                # compute randomly the key of this entry as a tuple
                key = mketuple (keylength, 0, 'int', 'str')

                # checking the length of the keys is pretty important since
                # namespaces do not verify it
                if keylength != len (key):
                    raise KeyError ('Mismatch in the length of the key: %i != %i' % (keylength, len (key)))

                # and write it into the specification of this testcase
                testcase [attribute][key] = randval ()

        # now, initialize a namespace passing these values directly
        cmd = ''
        for iattr in testcase.keys ():
            cmd += "%s = %s, " % (iattr, testcase[iattr])

        # now, create a namespace passing by this command line specification
        exec ("test = namespace.Namespace (%s)" % cmd[:-2])

        # update the testcase in this instance with this namespace
        exec ("self._namespace.update (test)")

        # finally, verify that all data was correctly saved using item selection
        # and attribute naming
        for iattr in testcase.keys ():

            for ikey, ival in testcase [iattr].items ():

                for imethod in ["test ['%s'] [%s]" % (iattr, ikey),  # item selection
                                "test.%s [%s]" % (iattr, ikey)]:     # attribute naming

                    (expected, returned) = (ival, eval (imethod))

                    # check for equality
                    if isinstance (ival, float):
                        self.assertAlmostEqual (expected, returned)
                    else:
                        self.assertEqual (expected, returned)

        # verify also that all information in this instance is still there
        for iattr in self._testcase.keys ():

            for ikey, ival in self._testcase [iattr].items ():

                for imethod in ["self._namespace ['%s'] [%s]" % (iattr, ikey),  # item selection
                                "self._namespace.%s [%s]" % (iattr, ikey)]:     # attribute naming

                    (expected, returned) = (ival, eval (imethod))

                    # check for equality
                    if isinstance (ival, float):
                        self.assertAlmostEqual (expected, returned)
                    else:
                        self.assertEqual (expected, returned)


    def tearDown (self): pass



# Main body
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # declare all test cases
    test_cases = (SingleTestCase, MultipleTestCase)

    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = unittest.TestLoader ().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # and execute the suite
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local Variables:
# mode:python
# fill-column:80
# End:
