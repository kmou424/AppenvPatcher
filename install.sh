#!/usr/bin/env bash
echo "Test root permission"
sudo test

echo "Clean up old installation"
if [ -f "/usr/bin/deskicon_patcher" ];
then
  sudo rm /usr/bin/deskicon_patcher
fi

echo
echo "Installing deskicon_patcher"
sudo ln -s $PWD/deskicon_patcher.py /usr/bin/deskicon_patcher
echo "Done"
