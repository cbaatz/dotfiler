#!/usr/bin/env python

import unittest
import random
import dotfiler

import os
import shutil
import tempfile

class TempDirTestCase(unittest.TestCase):
    """
    Create and set temporary home and dot dirs.
    
    """
    def setUp(self):
        super(TempDirTestCase, self).setUp()
        self.orig_home_dir = dotfiler.HOME_DIR
        self.home_dir = tempfile.mkdtemp()
        self.dot_dir = os.path.join(self.home_dir, "thedotfiles")
        dotfiler.HOME_DIR = self.home_dir

    def tearDown(self):
        super(TempDirTestCase, self).tearDown()
        dotfiler.HOME_DIR = self.orig_home_dir

class GlobalTests(unittest.TestCase):

    def test_home_dir(self):
        """
        HOME_DIR is set to the environment variable HOME.

        """
        self.assertEqual(dotfiler.HOME_DIR, os.environ["HOME"])

    def test_config_name(self):
        """
        CONFIG_NAME is ".dotfiles"

        """
        self.assertEqual(dotfiler.CONFIG_NAME, ".dotfiles")

    def test_symlink_filename(self):
        """
        symlink_filename is HOME_DIR/CONFIG_NAME.

        """
        self.assertEqual(dotfiler.symlink_filename(),
                         os.path.join(dotfiler.HOME_DIR, dotfiler.CONFIG_NAME))

class IsManagedTests(TempDirTestCase):
    def setUp(self):
        """
        Set up names.

        """
        super(IsManagedTests, self).setUp()
        self.dot_dir = os.path.join(dotfiler.HOME_DIR, "dotdir")
        dotfiler.init(self.dot_dir)

    def test_missing(self):
        self.setUp()
        filename = os.path.join(self.home_dir, ".testfile1")
        self.assertFalse(dotfiler.is_managed(filename))

    def test_normal_file(self):
        self.setUp()
        filename = os.path.join(self.home_dir, ".testfile1")
        open(filename, "w").close()
        self.assertFalse(dotfiler.is_managed(filename))

    def test_other_link(self):
        self.setUp()
        target = os.path.join(self.home_dir, "targetfile")
        open(target, "w").close()
        filename = os.path.join(self.home_dir, ".testfile1")
        os.symlink(target, filename)
        self.assertFalse(dotfiler.is_managed(filename))

    def test_broken_link(self):
        self.setUp()
        filename = os.path.join(self.home_dir, ".testfile1")
        open(filename, "w").close()
        dotfiler.manage(filename)
        os.remove(os.path.join(self.dot_dir, "testfile1"))
        self.assertFalse(dotfiler.is_managed(filename))

    def test_ok(self):
        self.setUp()
        filename = os.path.join(self.home_dir, ".testfile1")
        open(filename, "w").close()
        dotfiler.manage(filename)
        self.assertTrue(dotfiler.is_managed(filename))

class UnmanageTests(TempDirTestCase):
    def setUp(self):
        """
        Set up names.

        """
        super(UnmanageTests, self).setUp()
        self.dot_dir = os.path.join(dotfiler.HOME_DIR, "dotdir")
        dotfiler.init(self.dot_dir)

    def test_managed_file(self):
        self.setUp()
        # Create managed file
        filename = os.path.join(self.home_dir, ".testfile1")
        open(filename, "w").close()
        # Manage file and check results
        dotfiler.manage(filename)
        self.assertTrue(dotfiler.is_managed(filename))
        self.assertTrue(os.path.exists(os.path.join(self.dot_dir, "testfile1")))
        # Unmanage file and check results
        dotfiler.unmanage(filename)
        self.assertFalse(dotfiler.is_managed(filename))
        self.assertFalse(os.path.islink(filename))
        self.assertFalse(os.path.islink(filename))
        self.assertFalse(os.path.exists(os.path.join(self.dot_dir, "testfile1")))

    def test_managed_dir(self):
        self.setUp()
        # Create managed file
        dirname = os.path.join(self.home_dir, ".testdir")
        os.mkdir(dirname)
        open(os.path.join(dirname, "testfile"), "w").close()
        # Manage file and check results
        dotfiler.manage(dirname)
        self.assertTrue(dotfiler.is_managed(dirname))
        self.assertTrue(os.path.exists(os.path.join(self.dot_dir, "testdir")))
        # Unmanage file and check results
        dotfiler.unmanage(dirname)
        self.assertFalse(dotfiler.is_managed(dirname))
        self.assertFalse(os.path.islink(dirname))
        self.assertFalse(os.path.exists(os.path.join(self.dot_dir, "testdir")))

    def test_managed_nested(self):
        self.setUp()
        # Create unmanaged dot directory and a managed file inside it.
        dirname = os.path.join(self.home_dir, ".dir")
        os.mkdir(dirname)
        filename = os.path.join(dirname, "subdir/testfile1")
        os.makedirs(os.path.dirname(filename))
        open(filename, "w").close()
        # Manage file and check results
        dotfiler.manage(filename)
        self.assertTrue(dotfiler.is_managed(filename))
        self.assertTrue(dotfiler.is_partially_managed(dirname))
        self.assertTrue(os.path.exists(
                os.path.join(self.dot_dir, "dir/subdir/testfile1")))
        dotfiler.unmanage(filename)
        self.assertFalse(dotfiler.is_managed(filename))
        self.assertFalse(dotfiler.is_partially_managed(dirname))
        self.assertFalse(os.path.islink(filename))
        self.assertFalse(os.path.exists(
                os.path.join(self.dot_dir, "dir/subdir/testfile1")))

    def test_partially_managed(self):
        self.setUp()
        # Create partially managed dir
        dirname = os.path.join(self.home_dir, ".dir")
        os.mkdir(dirname)
        filename = os.path.join(dirname, "subdir/subdir/testfile1")
        os.makedirs(os.path.dirname(filename))
        open(filename, "w").close()
        dotfiler.manage(filename)
        self.assertTrue(dotfiler.is_partially_managed(dirname))
        dotfiler.unmanage(dirname)
        self.assertFalse(dotfiler.is_partially_managed(dirname))
        self.assertFalse(dotfiler.is_managed(dirname))

    def test_unmanaged(self):
        # Raise NotManagedException
        filename1 = os.path.join(self.home_dir, ".testfile1")
        open(filename1, "w").close()
        filename2 = os.path.join(self.home_dir, ".testfile2")
        self.assertRaises(dotfiler.NotManagedException, dotfiler.unmanage, filename1)
        self.assertRaises(dotfiler.NotManagedException, dotfiler.unmanage, filename2)

class ManageTests(TempDirTestCase):
    def setUp(self):
        """
        Set up names.

        """
        super(ManageTests, self).setUp()
        self.dot_dir = os.path.join(dotfiler.HOME_DIR, "dotdir")
        dotfiler.init(self.dot_dir)

    def test_manage(self):
        self.setUp()
        filename = os.path.join(self.home_dir, ".test1")
        open(filename, "w").close()
        target = dotfiler.manage(filename)
        dot_dir = os.path.dirname(dotfiler.get_config().name)
        self.assertEqual(os.path.dirname(target), dot_dir)
        self.assertTrue(os.path.islink(filename))
        self.assertEqual(os.readlink(filename), target)
        self.assertTrue(os.path.exists(target))

    def test_manage_nested_in_managed(self):
        self.setUp()
        dirname = os.path.join(self.home_dir, ".dir")
        os.mkdir(dirname)
        filename = os.path.join(dirname, "testfile")
        open(filename, "w").close()
        dotfiler.manage(dirname)
        self.assertRaises(dotfiler.AlreadyManagedException, dotfiler.manage, filename)

    def test_manage_nested(self):
        self.setUp()
        # Create unmanaged dot directory and a managed file inside it.
        dirname = os.path.join(self.home_dir, ".dir")
        managed_path = os.path.join(self.dot_dir, "dir", "testfile1")
        os.mkdir(dirname)
        filename1 = os.path.join(dirname, "testfile1")
        filename2 = os.path.join(dirname, "testfile2")
        open(filename1, "w").close()
        open(filename2, "w").close()
        dotfiler.manage(filename1)
        self.assertTrue(dotfiler.is_managed(filename1))
        self.assertTrue(os.path.exists(managed_path))
        self.assertTrue(os.path.isfile(managed_path))
        self.assertFalse(dotfiler.is_managed(dirname))
        self.assertFalse(dotfiler.is_managed(filename2))
        
    def test_manage_dir_partial_simple(self):
        self.setUp()
        # Create unmanaged dot directory and a managed file inside it.
        dirname = os.path.join(self.home_dir, ".dir")
        os.mkdir(dirname)
        filename = os.path.join(dirname, "testfile1")
        open(filename, "w").close()
        dotfiler.manage(filename)
        # Managing .dir should now give a PartiallyManagedException
        self.assertRaises(dotfiler.PartiallyManagedException,
                          dotfiler.manage, dirname)
        self.assertRaises(dotfiler.AlreadyManagedException,
                          dotfiler.manage, filename)

    def test_manage_dir_partial_subdir(self):
        self.setUp()
        # Create unmanaged dot directory and a managed file inside it.
        dirname = os.path.join(self.home_dir, ".dir")
        os.mkdir(dirname)
        filename = os.path.join(dirname, "subdir/subdir/testfile1")
        os.makedirs(os.path.dirname(filename))
        open(filename, "w").close()
        dotfiler.manage(filename)
        # Managing .dir should now give a PartiallyManagedException
        self.assertRaises(dotfiler.PartiallyManagedException,
                          dotfiler.manage, dirname)
        self.assertRaises(dotfiler.PartiallyManagedException,
                          dotfiler.manage, os.path.join(dirname, "subdir"))
        self.assertRaises(dotfiler.PartiallyManagedException,
                          dotfiler.manage, os.path.join(dirname, "subdir/subdir"))
        self.assertRaises(dotfiler.AlreadyManagedException,
                          dotfiler.manage, filename)

    def test_manage_not_home(self):
        self.setUp()
        self.other_dir = tempfile.mkdtemp()
        filename = os.path.join(self.other_dir, ".testlink")
        open(filename, "w").close()
        self.assertRaises(dotfiler.NotManageableException, dotfiler.manage, filename)

    def test_manage_managed(self):
        self.setUp()
        dirname = os.path.join(self.home_dir, ".testdir")
        filename = os.path.join(self.home_dir, ".testfile")
        os.mkdir(dirname)
        open(filename, "w").close()
        dotfiler.manage(dirname)
        dotfiler.manage(filename)
        self.assertRaises(dotfiler.AlreadyManagedException, dotfiler.manage, filename)
        self.assertRaises(dotfiler.AlreadyManagedException, dotfiler.manage, dirname)

    def test_manage_dotless(self):
        self.setUp()
        dirname = os.path.join(self.home_dir, "testdir")
        filename = os.path.join(self.home_dir, "testfile")
        os.mkdir(dirname)
        open(filename, "w").close()
        self.assertRaises(dotfiler.NotManageableException, dotfiler.manage, filename)
        self.assertRaises(dotfiler.NotManageableException, dotfiler.manage, dirname)
    
    def test_manage_other_link(self):
        self.setUp()
        filename = os.path.join(self.home_dir, ".testlink")
        os.symlink("/", filename)
        self.assertRaises(dotfiler.NotManageableException, dotfiler.manage, filename)

    def test_manage_missing(self):
        self.setUp()
        filename = os.path.join(self.home_dir, ".missing")
        self.assertRaises(dotfiler.NotManageableException, dotfiler.manage, filename)

class InitTests(TempDirTestCase):

    def setUp(self):
        """
        Set up names.

        """
        super(InitTests, self).setUp()
        self.symlink = dotfiler.symlink_filename()
        self.dot_dir = os.path.join(dotfiler.HOME_DIR, "dotdir")
        self.target = os.path.join(self.dot_dir, dotfiler.nodot(dotfiler.CONFIG_NAME))

    def init_files(self):
        """
        Remove symlink and dot_dir in (temporary) home dir.

        """
        try:
            os.remove(self.symlink)
        except OSError:
            pass
        try:
            shutil.rmtree(self.dot_dir)
        except OSError:
            pass

    def test_existing_file(self):
        self.init_files()
        f = open(self.symlink, "w")
        f.close()
        self.assertRaises(dotfiler.ConfigExistsException, dotfiler.init, self.dot_dir)
        self.assertFalse(os.path.exists(self.dot_dir))
        
    def test_existing_dir(self):
        self.init_files()
        os.makedirs(self.dot_dir)
        self.assertRaises(dotfiler.DirExistsException, dotfiler.init, self.dot_dir)
        self.assertFalse(os.path.exists(self.symlink))

    def test_ok(self):
        self.init_files()
        dotfiler.init(self.dot_dir)
        f = dotfiler.get_config()
        self.assertIsInstance(f, file)
        self.assertEquals(f.name, self.target)

class GetConfigTests(TempDirTestCase):

    def setUp(self):
        """
        Set up names.

        """
        super(GetConfigTests, self).setUp()
        self.symlink = dotfiler.symlink_filename()
        self.dot_dir = os.path.join(dotfiler.HOME_DIR, "dotdir")
        self.target = os.path.join(self.dot_dir, "dotfiles")

    def init_files(self):
        """
        Remove symlink and dot_dir in (temporary) home dir and create
        empty dot_dir.

        """
        try:
            os.remove(self.symlink)
        except OSError:
            pass
        try:
            shutil.rmtree(self.dot_dir)
        except OSError:
            pass

        os.makedirs(self.dot_dir)

    def create_normal_file(self):
        f = open(self.symlink, "w")
        f.close()
        
    def create_symlink(self):
        os.symlink(self.target, self.symlink)
    
    def create_dir_target(self):
        os.makedirs(self.target)

    def create_target(self):
        f = open(self.target, "w")
        f.close()

    def test_nothing(self):
        self.init_files()
        self.assertRaises(dotfiler.ConfigMissingException, dotfiler.get_config)

    def test_no_target(self):
        self.init_files()
        self.create_symlink()
        self.assertRaises(dotfiler.ConfigMissingException, dotfiler.get_config)

    def test_normal(self):
        self.init_files()
        self.create_normal_file()
        self.assertRaises(dotfiler.ConfigInvalidException, dotfiler.get_config)

    def test_dir_target(self):
        self.init_files()
        self.create_symlink()
        self.create_dir_target()
        self.assertRaises(dotfiler.ConfigInvalidException, dotfiler.get_config)

    def test_ok(self):
        self.init_files()
        self.create_symlink()
        self.create_target()
        f = dotfiler.get_config()
        self.assertIsInstance(f, file)
        self.assertEquals(f.name, self.target)

if __name__ == "__main__":
    unittest.main()
