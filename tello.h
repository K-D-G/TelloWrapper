#ifndef TELLO_WRAPPER_H
#define TELLO_WRAPPER_H
#include <iostream>
#include <string>
#include <boost/asio.hpp>

namespace TelloWrapper{
  class Tello{
  private:
    const std::string UDP_IP="192.168.10.1"
    const int UDP_PORT_COMMAND=8889
    const int UDP_PORT_STATE=88890
    const std::string UDP_IP_VIDEO="192.168.10.1"
    const std::string UDP_PORT_VIDEO=11111
    const float TIME_OUT=0.5
    const float TIME_BETWEEN_COMMANDS=0.5
    const float TIME_BETWEEN_RC_CONTROL_COMMANDS=0.5

    bool log;
    bool override=false;
    bool can_rc=false;
    float last_rc_control_sent=0;

    float left_right_velocity=0;
    float forward_backward_velocity=0;
    float up_down_velocity=0
    float yaw_velocity=0
    float override_speed=1
    float drone_speed=20

    float last_received_command;

    bool stream_on=false;

    inline std::string _read(boost::asio::ip::tcp::socket &socket){
      boost::asio::streambuf buffer;
      boost::asio::read_until(socket, buffer, "\n");
      std::string data=boost::asio::buffer_cast<const char*>(buffer.data());
      return data
    }
    inline void _send(boost::asio::ip::tcp::socket &socket, const std::string &message){
      boost::asio::write(socket, boost::asio::buffer(message));
    }
  public:
    Tello(bool log=true);
    ~Tello();


  };
}


#endif
