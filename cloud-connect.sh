if [ "$#" -ne 2 ]; then
echo "Usage: $0 [username] [hostname]"
exit 1
fi
FOREIGN_HOSTNAME=$2
RANDOM=$FOREIGN_HOSTNAME; PORT=$((RANDOM + 2000)); echo "Trying to connect to hostname $FOREIGN_HOSTNAME which we expect to be accessable on local port $PORT"; ssh -p $PORT $1@localhost
